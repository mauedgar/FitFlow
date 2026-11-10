"""Bounded per-login JWT session revocation with Redis fail-closed checks.

No persisted User schema changes. New JWTs carry one signed UUID4 session id.
Legacy signed tokens without sid remain valid only until their original exp;
a legacy bearer explicitly presented to logout is blacklisted by digest.
"""
from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from redis.exceptions import RedisError

from app.core.blacklist import is_token_blacklisted
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.security import token_seconds_until_expiry
from app.services.errors import ExternalServiceError

_REVOKED_SESSION_PREFIX = "revoked_session:"
# Extra Redis tombstone retention after the last possible refresh. A fresh
# access credential may outlive its parent refresh by this entire interval.
# The 60-second cushion protects expiration rounding and modest clock drift.
_REVOCATION_CLOCK_SKEW_SECONDS = 60


def _valid_sid(sid: object) -> str | None:
    if not isinstance(sid, str):
        return None
    try:
        value = UUID(sid)
    except (ValueError, AttributeError):
        return None
    return value.hex if value.version == 4 else None


def _revocation_key(sid: str) -> str:
    return _REVOKED_SESSION_PREFIX + sha256(sid.encode("utf-8")).hexdigest()


def is_session_revoked(sid: str) -> bool:
    """Check session revocation; unexpected Redis I/O failures are never allow."""
    valid = _valid_sid(sid)
    if valid is None:
        return True
    try:
        return get_redis_client().exists(_revocation_key(valid)) == 1
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc


def revoke_session(sid: str, refresh_token: str) -> None:
    """Keep session revoked through the latest access minted by its refresh."""
    valid = _valid_sid(sid)
    if valid is None:
        raise ValueError("Identificador de sesión inválido")
    # A refresh issued at the final valid instant may mint a full-duration
    # access token. Expiring the marker with the refresh would re-enable it.
    ttl = (
        token_seconds_until_expiry(refresh_token)
        + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        + _REVOCATION_CLOCK_SKEW_SECONDS
    )
    try:
        get_redis_client().set(_revocation_key(valid), "1", ex=ttl)
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc


def is_access_credential_revoked(token: str, payload: dict) -> bool:
    """Both API bearer pipelines must call this on every protected request."""
    # Existing individual blacklist applies to typed and legacy credentials.
    if is_token_blacklisted(token):
        return True
    if "sid" not in payload:
        return False  # Historical JWT: bounded compatibility, no session id.
    return is_session_revoked(payload["sid"])


def session_ids_match(access_payload: dict, refresh_payload: dict) -> bool:
    """Only credentials from exactly the same signed login may revoke a session."""
    access_sid, refresh_sid = access_payload.get("sid"), refresh_payload.get("sid")
    if access_sid is None and refresh_sid is None:
        return True  # Historical signed pair only.
    if _valid_sid(access_sid) is None or _valid_sid(refresh_sid) is None:
        return False
    return _valid_sid(access_sid) == _valid_sid(refresh_sid)

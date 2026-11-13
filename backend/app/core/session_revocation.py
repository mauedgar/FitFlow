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

# One server-side Redis operation prevents a concurrent refresh/logout from
# observing intermediate writes. Script success is the only 204 acknowledgement.
# Redis scripting is isolated, but a Redis runtime error after a write is not
# automatically rolled back; such failures stay UNCONFIRMED to the caller.
_LOGOUT_SCRIPT = """
if redis.call('EXISTS', KEYS[7]) == 1 then
  return 2
end
if redis.call('EXISTS', KEYS[3]) == 1 or redis.call('EXISTS', KEYS[4]) == 1 then
  return 0
end
local subject = redis.call('GET', KEYS[1])
if subject ~= ARGV[5] then
  subject = redis.call('GET', KEYS[2])
end
if subject ~= ARGV[5] then
  return 0
end
if ARGV[2] == 'sid' then
  redis.call('SET', KEYS[5], '1', 'EX', ARGV[3])
elseif ARGV[4] == '1' then
  redis.call('SET', KEYS[6], '1', 'EX', ARGV[6])
end
redis.call('SET', KEYS[3], '1', 'EX', ARGV[1])
redis.call('DEL', KEYS[1], KEYS[2])
redis.call('SET', KEYS[7], '1', 'EX', ARGV[1])
return 1
"""


def commit_logout(
    refresh_token: str, *, sid: str | None, access_token: str | None, subject: str,
) -> bool:
    """Atomically invalidate a registered signed refresh and its session.

    Returns False for a never-registered/invalid refresh; an exact previous
    acknowledgement is safe to repeat. No raw JWT is stored in new Redis keys.
    """
    from redis.exceptions import RedisError

    from app.core.token_keys import legacy_jwt_key, opaque_jwt_key

    if sid is not None:
        canonical_sid = _valid_sid(sid)
        if canonical_sid is None:
            return False
    else:
        canonical_sid = None
    refresh_ttl = token_seconds_until_expiry(refresh_token)
    # A renewed access can live beyond its parent refresh's final second.
    sid_ttl = (
        refresh_ttl + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        + _REVOCATION_CLOCK_SKEW_SECONDS
    )
    access_ttl = token_seconds_until_expiry(access_token) if access_token else 1
    keys = [
        opaque_jwt_key("refresh_token:", refresh_token),
        legacy_jwt_key("refresh_token:", refresh_token),
        opaque_jwt_key("blacklist_token:", refresh_token),
        legacy_jwt_key("blacklist_token:", refresh_token),
        _revocation_key(canonical_sid) if canonical_sid else opaque_jwt_key("unused_sid:", refresh_token),
        opaque_jwt_key("blacklist_token:", access_token) if access_token else opaque_jwt_key("unused_access:", refresh_token),
        opaque_jwt_key("logout_confirmed:", refresh_token),
    ]
    try:
        result = get_redis_client().eval(
            _LOGOUT_SCRIPT, len(keys), *keys, refresh_ttl,
            "sid" if canonical_sid else "legacy", sid_ttl,
            "1" if canonical_sid is None and access_token else "0",
            subject, access_ttl,
        )
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc
    if result not in (0, 1, 2):
        raise ExternalServiceError("Resultado de revocación Redis no confirmado.")
    return result in (1, 2)

"""Durable session-family operations; no Redis reads or writes."""
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest
from math import isfinite

from jose import JWTError, jwt
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token, is_refresh_token_payload
from app.db.models.auth_session import AuthSession


def _uuid4(value: object) -> UUID | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return None
    return parsed if parsed.version == 4 and str(parsed) == value else None


def fingerprint(token: str) -> str:
    """Fixed-length SHA256 fingerprint; no bearer token in persistent state."""
    return sha256(token.encode("utf-8")).hexdigest()


def signed_refresh_family(token: str) -> tuple[UUID, UUID, datetime] | None:
    """Only valid signed modern refresh JWTs can identify durable sessions."""
    payload = decode_token(token)
    if not is_refresh_token_payload(payload) or not isinstance(payload, dict):
        return None
    family = _uuid4(payload.get("sid"))
    try:
        owner = UUID(payload["sub"])
        expires = datetime.fromtimestamp(payload["exp"], tz=UTC)
    except (KeyError, ValueError, TypeError, OverflowError):
        return None
    if family is None or expires <= datetime.now(tz=UTC):
        return None
    return family, owner, expires


def signed_refresh_family_for_replay(token: str) -> tuple[UUID, UUID, datetime] | None:
    """Verify an exact signed refresh family, ignoring expiry ONLY for replay.

    Never authorize active sessions from this parser: revoke() still checks
    row state, signed claims, owner and constant-time digest. Expiration is
    deliberately enforced before any first-time COMMIT.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
    except (JWTError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("token_use") != "refresh":
        return None
    if "role" in payload or not isinstance(payload.get("sub"), str):
        return None
    sid = _uuid4(payload.get("sid"))
    exp = payload.get("exp")
    if sid is None or isinstance(exp, bool) or not isinstance(exp, (int, float)):
        return None
    if not isfinite(exp):
        return None
    try:
        owner = UUID(payload["sub"])
        expiry = datetime.fromtimestamp(exp, tz=UTC)
    except (ValueError, TypeError, OverflowError):
        return None
    if str(owner) != payload["sub"]:
        return None
    return sid, owner, expiry


async def register(db: AsyncSession, *, subject: UUID, refresh_token: str) -> AuthSession:
    """COMMIT family registration before issuing tokens to the client."""
    claim = signed_refresh_family(refresh_token)
    if claim is None or claim[1] != subject:
        raise ValueError("Refresh JWT moderno no pertenece al usuario")
    sid, _, expiry = claim
    row = AuthSession(
        id=sid, user_id=subject,
        refresh_digest=fingerprint(refresh_token), expires_at=expiry,
    )
    try:
        db.add(row)
        await db.commit()
    except Exception:
        # An uncertain COMMIT must never be treated as an issued credential.
        # Rollback is best-effort cleanup; the caller returns no token or 204.
        try:
            await db.rollback()
        except Exception:
            pass
        raise
    return row


async def is_active(
    db: AsyncSession, *, sid: str, subject: str,
    refresh_token: str | None = None,
) -> bool:
    """Revoked, missing, wrong-owner, expired or wrong-digest is always deny."""
    family = _uuid4(sid)
    try:
        owner = UUID(subject)
    except (TypeError, ValueError, AttributeError):
        return False
    if family is None:
        return False
    row = await db.scalar(
        select(AuthSession).where(AuthSession.id == family, AuthSession.user_id == owner)
    )
    if row is None or row.revoked_at is not None:
        return False
    if row.expires_at <= datetime.now(tz=UTC):
        return False
    return refresh_token is None or compare_digest(
        row.refresh_digest, fingerprint(refresh_token)
    )


async def revoke(db: AsyncSession, *, refresh_token: str) -> str:
    """Atomic row-lock revoke; only a successful DB COMMIT establishes an ACK.

    A second call with same exact signed refresh returns ALREADY_COMMITTED.
    """
    claim = signed_refresh_family_for_replay(refresh_token)
    if claim is None:
        return "INVALID"
    sid, owner, signed_expiry = claim
    try:
        row = await db.scalar(
            select(AuthSession).where(
                AuthSession.id == sid, AuthSession.user_id == owner,
            ).with_for_update()
        )
        if row is None or not compare_digest(
            row.refresh_digest, fingerprint(refresh_token)
        ):
            await db.rollback()
            return "INVALID"
        if row.revoked_at is not None:
            await db.rollback()
            return "ALREADY_COMMITTED"
        if row.expires_at <= datetime.now(tz=UTC) or signed_expiry <= datetime.now(tz=UTC):
            # An expired signed token may ACK an already-revoked row above,
            # but can NEVER revoke one which was still active.
            await db.rollback()
            return "INVALID"
        row.revoked_at = datetime.now(tz=UTC)
        await db.commit()
        return "COMMITTED"
    except Exception:
        await db.rollback()
        raise

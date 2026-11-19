"""Durable session-family operations; no Redis reads or writes."""
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from hmac import compare_digest
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    db.add(row)
    await db.commit()
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
    claim = signed_refresh_family(refresh_token)
    if claim is None:
        return "INVALID"
    sid, owner, _ = claim
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
        if row.expires_at <= datetime.now(tz=UTC):
            await db.rollback()
            return "INVALID"
        row.revoked_at = datetime.now(tz=UTC)
        await db.commit()
        return "COMMITTED"
    except Exception:
        await db.rollback()
        raise

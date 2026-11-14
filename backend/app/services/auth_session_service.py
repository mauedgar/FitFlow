"""Explicitly bounded A1 storage orchestration; does not authenticate tokens."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.crud.crud_auth_session import auth_session as auth_session_crud
from app.db.models.auth_session import AuthSession

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _check_digest(digest: bytes, *, name: str) -> None:
    if not isinstance(digest, bytes) or len(digest) != 32:
        raise ValueError(f"{name} must be exactly 32 digest bytes")


async def stage_new_session(
    db: AsyncSession,
    *,
    sid: uuid.UUID,
    user_id: uuid.UUID,
    refresh_credential_digest: bytes,
    logout_proof_digest: bytes,
    logout_proof_key_id: str,
    absolute_expires_at: datetime,
    logout_proof_expires_at: datetime,
) -> AuthSession:
    """Stage a new A2-compatible record, without committing or issuing credentials.

    No caller exists in the A1 application. The future A2 login service must
    commit this record *before* returning signed tokens to a client.
    """
    _check_digest(refresh_credential_digest, name="refresh_credential_digest")
    _check_digest(logout_proof_digest, name="logout_proof_digest")
    if not isinstance(sid, uuid.UUID) or not isinstance(user_id, uuid.UUID):
        raise ValueError("sid and user_id must be UUID instances")
    if not logout_proof_key_id or len(logout_proof_key_id) > 64 or not logout_proof_key_id.strip():
        raise ValueError("logout_proof_key_id must be nonempty and at most 64 chars")
    if not (absolute_expires_at.tzinfo and logout_proof_expires_at.tzinfo):
        raise ValueError("expiry datetimes must be timezone-aware")
    record = AuthSession(
        sid=sid,
        user_id=user_id,
        refresh_generation=0,
        refresh_credential_digest=refresh_credential_digest,
        logout_proof_digest=logout_proof_digest,
        logout_proof_key_id=logout_proof_key_id,
        absolute_expires_at=absolute_expires_at,
        logout_proof_expires_at=logout_proof_expires_at,
    )
    return await auth_session_crud.stage(db, record=record)

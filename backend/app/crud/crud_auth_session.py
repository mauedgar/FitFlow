"""Persistence primitives for auth_sessions; no authorization policy (G2-A1)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from app.db.models.auth_session import AuthSession

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CRUDAuthSession:
    async def get(self, db: AsyncSession, *, sid: UUID) -> AuthSession | None:
        return (await db.execute(select(AuthSession).where(AuthSession.sid == sid))).scalar_one_or_none()

    async def get_locked(self, db: AsyncSession, *, sid: UUID) -> AuthSession | None:
        """A2 must use this same-row lock for refresh and logout transitions."""
        return (
            await db.execute(select(AuthSession).where(AuthSession.sid == sid).with_for_update())
        ).scalar_one_or_none()

    async def stage(self, db: AsyncSession, *, record: AuthSession) -> AuthSession:
        """Flush only; caller owns the transaction boundary and its commit."""
        db.add(record)
        await db.flush()
        return record


auth_session = CRUDAuthSession()

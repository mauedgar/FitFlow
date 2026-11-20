"""Exact PostgreSQL SID registration for isolated functional HTTP test credentials.

Never bypass Product authentication. Fixture callers must COMMIT their
current PostgreSQL transaction before using these signed access JWTs.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.auth_session import fingerprint, signed_refresh_family
from app.db.models.auth_session import AuthSession
from app.db.session import AsyncSessionLocal


def require_local_test_database() -> None:
    """Fail before any synthetic INSERT, even if no bearer will be minted."""
    target = make_url(settings.DATABASE_URL)
    if not (
        target.database == "fitflow_test"
        and (target.host or "").lower() in {"127.0.0.1", "localhost", "::1"}
        and settings.ENV == "test"
        and settings.TESTING
    ):
        raise RuntimeError("BLOCKED_PRECONDITION: only local disposable fitflow_test is allowed")


def staged_access(db: AsyncSession, user_id: UUID, role: str) -> str:
    """Stage a real modern session row; caller commits with synthetic users."""
    require_local_test_database()
    sid = uuid4()
    refresh = create_refresh_token({"sub": str(user_id), "sid": str(sid)})
    family = signed_refresh_family(refresh)
    if family is None or family[0] != sid or family[1] != user_id:
        raise RuntimeError("BLOCKED_PRECONDITION: invalid synthetic signed session")
    db.add(AuthSession(
        id=sid, user_id=user_id, refresh_digest=fingerprint(refresh),
        expires_at=family[2],
    ))
    return create_access_token({"sub": str(user_id), "role": role, "sid": str(sid)})


async def committed_access(user_id: UUID, role: str) -> str:
    """Issue a PG-committed family for an already persisted synthetic user."""
    async with AsyncSessionLocal() as db:
        token = staged_access(db, user_id, role)
        await db.commit()
        return token

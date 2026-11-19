"""Disposable PostgreSQL15-only checks for durable session ledger."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.crud.auth_session import is_active, register, revoke, signed_refresh_family
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_postgres() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def release_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def owner() -> AsyncIterator[uuid.UUID]:
    owner_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=owner_id, email=f"auth-ledger-{owner_id.hex}@example.com",
            hashed_password=security.get_password_hash("synthetic-only"),
            role=UserRole.client, active=True,
        ))
        await db.commit()
    try:
        yield owner_id
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuthSession).where(AuthSession.user_id == owner_id))
            await db.execute(delete(User).where(User.id == owner_id))
            await db.commit()


def new_login(user: uuid.UUID) -> tuple[str, str]:
    family = str(uuid.uuid4())
    token = security.create_refresh_token({"sub": str(user), "sid": family})
    return family, token


async def test_signed_session_persists_and_revocation_survives_new_engine(
    owner: uuid.UUID,
) -> None:
    sid, token = new_login(owner)
    async with AsyncSessionLocal() as db:
        await register(db, subject=owner, refresh_token=token)
        assert await is_active(db, sid=sid, subject=str(owner), refresh_token=token)
    await engine.dispose()
    async with AsyncSessionLocal() as db:
        assert await is_active(db, sid=sid, subject=str(owner))
        assert await revoke(db, refresh_token=token) == "COMMITTED"
    await engine.dispose()
    async with AsyncSessionLocal() as db:
        assert not await is_active(db, sid=sid, subject=str(owner))
        assert await revoke(db, refresh_token=token) == "ALREADY_COMMITTED"


async def test_family_specific_revoke_keeps_other_login_active(owner: uuid.UUID) -> None:
    sid1, jwt1 = new_login(owner)
    sid2, jwt2 = new_login(owner)
    async with AsyncSessionLocal() as db:
        await register(db, subject=owner, refresh_token=jwt1)
        await register(db, subject=owner, refresh_token=jwt2)
        assert await revoke(db, refresh_token=jwt1) == "COMMITTED"
        assert not await is_active(db, sid=sid1, subject=str(owner))
        assert await is_active(db, sid=sid2, subject=str(owner), refresh_token=jwt2)
        assert not await is_active(db, sid=sid2, subject=str(uuid.uuid4()))
        assert not await is_active(db, sid=sid2, subject=str(owner), refresh_token=jwt1)


async def test_legacy_mismatch_and_rollback_are_fail_closed(owner: uuid.UUID) -> None:
    sid, token = new_login(owner)
    untyped = security.create_refresh_token({"sub": str(owner)})
    assert signed_refresh_family(untyped) is None
    async with AsyncSessionLocal() as db:
        assert await revoke(db, refresh_token=token) == "INVALID"
        assert await revoke(db, refresh_token=untyped) == "INVALID"
        with pytest.raises(ValueError):
            await register(db, subject=uuid.uuid4(), refresh_token=token)
        await register(db, subject=owner, refresh_token=token)
        row = await db.get(AuthSession, uuid.UUID(sid))
        assert row is not None
        row.revoked_at = datetime.now(tz=UTC)
        await db.rollback()
    async with AsyncSessionLocal() as db:
        assert await is_active(db, sid=sid, subject=str(owner))
        assert await revoke(db, refresh_token=token) == "COMMITTED"

"""Disposable PostgreSQL15-only checks for durable session ledger."""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from jose import jwt

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import DBAPIError

from app.core import security
from auth_session_test_helpers import require_local_test_database
from app.core.config import settings
from app.core.enums import UserRole
from app.crud.auth_session import fingerprint, is_active, register, revoke, signed_refresh_family
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_postgres() -> None:
    require_local_test_database()


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


async def test_concurrent_exact_refresh_logout_is_serialized_by_postgres(
    owner: uuid.UUID,
) -> None:
    """Two transactions: exactly one durable COMMIT, one idempotent replay."""
    sid, refresh = new_login(owner)
    async with AsyncSessionLocal() as db:
        await register(db, subject=owner, refresh_token=refresh)

    async def revoke_from_new_connection() -> str:
        async with AsyncSessionLocal() as db:
            return await revoke(db, refresh_token=refresh)

    results = await asyncio.gather(
        revoke_from_new_connection(), revoke_from_new_connection(),
    )
    assert sorted(results) == ["ALREADY_COMMITTED", "COMMITTED"]
    async with AsyncSessionLocal() as db:
        assert not await is_active(db, sid=sid, subject=str(owner))


async def test_refresh_exclusive_row_lock_serializes_logout_and_preserves_bearer_reads(
    owner: uuid.UUID,
) -> None:
    """Real PG NOWAIT witnesses a refresh/logout mutual exclusion barrier."""
    sid, signed = new_login(owner)
    async with AsyncSessionLocal() as db:
        await register(db, subject=owner, refresh_token=signed)

    async with AsyncSessionLocal() as minting:
        assert await is_active(
            minting, sid=sid, subject=str(owner),
            refresh_token=signed, for_update=True,
        )
        async with AsyncSessionLocal() as normal_bearer:
            assert await is_active(normal_bearer, sid=sid, subject=str(owner))
            await normal_bearer.rollback()
        async with AsyncSessionLocal() as competing_logout:
            with pytest.raises(DBAPIError):
                await competing_logout.scalar(
                    select(AuthSession)
                    .where(AuthSession.id == uuid.UUID(sid))
                    .with_for_update(nowait=True)
                )
            await competing_logout.rollback()
        await minting.rollback()

    async with AsyncSessionLocal() as db:
        assert await revoke(db, refresh_token=signed) == "COMMITTED"
        assert not await is_active(
            db, sid=sid, subject=str(owner),
            refresh_token=signed, for_update=True,
        )


async def test_expired_refresh_replays_only_an_already_revoked_exact_family(
    owner: uuid.UUID,
) -> None:
    """No expired token can perform a first revoke, even if signed correctly."""
    expired = datetime.now(tz=UTC) - timedelta(seconds=60)
    replay_sid, active_sid = uuid.uuid4(), uuid.uuid4()
    def signed(sid: uuid.UUID) -> str:
        return jwt.encode(
            {"sub": str(owner), "sid": str(sid), "token_use": "refresh",
             "exp": int(expired.timestamp())},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM,
        )
    replay_token, active_token = signed(replay_sid), signed(active_sid)
    async with AsyncSessionLocal() as db:
        db.add_all([
            AuthSession(id=replay_sid, user_id=owner,
                        refresh_digest=fingerprint(replay_token),
                        expires_at=expired, revoked_at=expired),
            AuthSession(id=active_sid, user_id=owner,
                        refresh_digest=fingerprint(active_token),
                        expires_at=expired),
        ])
        await db.commit()
    async with AsyncSessionLocal() as db:
        assert await revoke(db, refresh_token=replay_token) == "ALREADY_COMMITTED"
        assert await revoke(db, refresh_token=active_token) == "INVALID"
        forged = jwt.encode(
            {"sub": str(uuid.uuid4()), "sid": str(replay_sid),
             "token_use": "refresh", "exp": int(expired.timestamp())},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM,
        )
        assert await revoke(db, refresh_token=forged) == "INVALID"
        assert await is_active(db, sid=str(active_sid), subject=str(owner)) is False
        row = await db.get(AuthSession, active_sid)
        assert row is not None and row.revoked_at is None

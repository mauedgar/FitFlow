"""Modern /auth/logout alias: real disposable PostgreSQL, no Redis authority."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_db() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def release_engine_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def account() -> AsyncIterator[tuple[uuid.UUID, str, str]]:
    uid = uuid.uuid4()
    email = f"logout-modern-{uid.hex}@example.com"
    password = "SyntheticLogout!123"
    async with AsyncSessionLocal() as db:
        db.add(User(id=uid, email=email,
                    hashed_password=security.get_password_hash(password),
                    role=UserRole.client, active=True))
        await db.commit()
    try:
        yield uid, email, password
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuthSession).where(AuthSession.user_id == uid))
            await db.execute(delete(User).where(User.id == uid))
            await db.commit()


async def login(client: httpx.AsyncClient, email: str, password: str) -> tuple[str, str]:
    response = await client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"], response.json()["refresh_token"]


async def logout(client: httpx.AsyncClient, access: str | None, refresh: str) -> httpx.Response:
    headers = {"Authorization": f"Bearer {access}"} if access is not None else {}
    return await client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers=headers, json={"refresh_token": refresh},
    )


async def test_logout_requires_authenticated_current_user(
    api_client: httpx.AsyncClient,
) -> None:
    refresh = security.create_refresh_token({
        "sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()),
    })
    result = await logout(api_client, None, refresh)
    assert result.status_code == 401
    assert result.json() == {"detail": "Not authenticated"}


async def test_logout_owner_persists_revoke_and_blocks_access(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uid, email, password = account
    monkeypatch.setattr(settings, "REDIS_URL", None)
    access, refresh = await login(api_client, email, password)
    result = await logout(api_client, access, refresh)
    assert result.status_code == 204, result.text
    claims = security.decode_token(access)
    assert claims is not None
    async with AsyncSessionLocal() as db:
        row = await db.get(AuthSession, uuid.UUID(claims["sid"]))
        assert row is not None and row.user_id == uid and row.revoked_at is not None
    blocked = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert blocked.status_code == 401


async def test_logout_rejects_sidless_and_malformed_without_mutating_pg(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    uid, email, password = account
    access, refresh = await login(api_client, email, password)
    legacy = security.create_refresh_token({"sub": str(uid)})
    for token, expected in ((legacy, 401), ("definitely-not-a-jwt", 400), (access, 400)):
        denied = await logout(api_client, access, token)
        assert denied.status_code == expected, denied.text
    still_active = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
    )
    assert still_active.status_code == 200, still_active.text


async def test_logout_rejects_other_owner_refresh(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    _uid, email, password = account
    second = uuid.uuid4()
    other_email = f"logout-foreign-{second.hex}@example.com"
    other_password = "SyntheticForeign!123"
    async with AsyncSessionLocal() as db:
        db.add(User(id=second, email=other_email,
                    hashed_password=security.get_password_hash(other_password),
                    role=UserRole.client, active=True))
        await db.commit()
    try:
        access, _refresh = await login(api_client, email, password)
        _foreign_access, foreign_refresh = await login(api_client, other_email, other_password)
        denied = await logout(api_client, access, foreign_refresh)
        assert denied.status_code == 403, denied.text
        still_active = await api_client.post(
            f"{settings.API_V1_STR}/auth/session/refresh",
            json={"refresh_token": foreign_refresh},
        )
        assert still_active.status_code == 200, still_active.text
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuthSession).where(AuthSession.user_id == second))
            await db.execute(delete(User).where(User.id == second))
            await db.commit()


async def test_logout_uncertain_ack_never_returns_false_204(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    access, refresh = await login(api_client, email, password)
    async def unavailable(*_args: object, **_kwargs: object) -> str:
        raise SQLAlchemyError("synthetic PG commit unknown")
    monkeypatch.setattr(auth_router.session_ledger, "revoke", unavailable)
    unknown = await logout(api_client, access, refresh)
    assert unknown.status_code == 503
    assert unknown.json() == {"detail": "Revocación durable no confirmada."}


async def test_logout_lost_ack_replays_without_revoked_access_bearer(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    access, refresh = await login(api_client, email, password)
    actual = auth_router.session_ledger.revoke

    async def commit_then_lose_ack(db: object, *, refresh_token: str) -> str:
        outcome = await actual(db, refresh_token=refresh_token)
        assert outcome == "COMMITTED"
        raise ConnectionError("synthetic lost ACK")

    monkeypatch.setattr(auth_router.session_ledger, "revoke", commit_then_lose_ack)
    unknown = await logout(api_client, access, refresh)
    assert unknown.status_code == 503
    monkeypatch.setattr(auth_router.session_ledger, "revoke", actual)
    denied = await logout(api_client, access, refresh)
    assert denied.status_code == 401  # Access family revoked, cannot authenticate.
    replay = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert replay.status_code == 204

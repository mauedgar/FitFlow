"""IR001 F01: public registration role boundary with actual PG15 and JWT."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import decode_token, get_password_hash
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def isolated_pg_only() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.mark.parametrize("role", ["admin", "teacher", "front_desk", "root", None])
async def test_public_registration_rejects_privilege_before_database_write(
    api_client: httpx.AsyncClient, role: str | None,
) -> None:
    email = f"ir001-denied-{uuid4().hex}@example.com"
    response = await api_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": email, "password": "SafeNewPassword!42", "role": role},
    )
    assert response.status_code == 422, response.text
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User.id).where(User.email == email)) is None


@pytest.mark.parametrize("explicit_role", [False, True])
async def test_public_registration_persists_client_and_issues_only_client_jwt(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    explicit_role: bool,
) -> None:
    email = f"ir001-client-{uuid4().hex}@example.com"
    password = "SafeNewPassword!42"
    payload = {"email": email, "password": password}
    if explicit_role:
        payload["role"] = "client"
    created_id: UUID | None = None
    try:
        registered = await api_client.post(f"{settings.API_V1_STR}/users/register", json=payload)
        assert registered.status_code == 201, registered.text
        created_id = UUID(registered.json()["id"])
        assert registered.json()["role"] == UserRole.client.value
        async with AsyncSessionLocal() as db:
            row = await db.scalar(select(User).where(User.id == created_id))
            assert row is not None
            assert row.role == UserRole.client
        monkeypatch.setattr(auth_router, "store_refresh_token", lambda *_args: None)
        login = await api_client.post(
            f"{settings.API_V1_STR}/auth/token",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = decode_token(login.json()["access_token"])
        assert token is not None
        assert token["sub"] == str(created_id)
        assert token["role"] == UserRole.client.value
    finally:
        if created_id is not None:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(User).where(User.id == created_id))
                await db.commit()


async def test_trusted_admin_fixture_remains_admin_without_public_role_provisioning(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = f"ir001-trusted-admin-{uuid4().hex}@example.com"
    password = "SafeTrustedFixture!42"
    user = User(email=email, hashed_password=get_password_hash(password), role=UserRole.admin)
    async with AsyncSessionLocal() as db:
        db.add(user)
        await db.commit()
        user_id = user.id
    try:
        monkeypatch.setattr(auth_router, "store_refresh_token", lambda *_args: None)
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/token",
            data={"username": email, "password": password},
        )
        assert response.status_code == 200, response.text
        token = decode_token(response.json()["access_token"])
        assert token is not None
        assert token["role"] == UserRole.admin.value
        assert token["sub"] == str(user_id)
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()

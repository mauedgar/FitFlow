"""Real HTTP/SQL rollback contract for public client signup (#97).

Only synthetic accounts on disposable PostgreSQL 'fitflow_test' are allowed.
Legacy /users/register is intentionally unchanged and account-only.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import status
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models.client import Client
from app.db.models.person import Person
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import users as users_router
from app.services import public_client_registration as signup_service

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]
API = settings.API_V1_STR


@pytest.fixture(autouse=True)
def require_disposable_test_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_async_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


async def _cleanup_synthetic_account(email: str) -> None:
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if user is not None:
            person = await db.scalar(select(Person).where(Person.user_id == user.id))
            if person is not None:
                await db.execute(delete(Client).where(Client.id == person.id))
                await db.execute(delete(Person).where(Person.id == person.id))
            await db.execute(delete(User).where(User.id == user.id))
            await db.commit()


async def test_client_signup_persists_real_person_and_client_and_me(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"onboarding-{uuid.uuid4().hex}@example.com"
    try:
        response = await api_client.post(
            f"{API}/users/register-client",
            json={
                "email": email,
                "password": "Only-Synthetic-Password-42",
                "full_name": "María Elena Pérez",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        body = response.json()
        assert body["role"] == UserRole.client.value
        assert body["email"] == email

        async with AsyncSessionLocal() as db:
            stored_user = await db.scalar(select(User).where(User.email == email))
            assert stored_user is not None
            assert str(stored_user.id) == body["id"]
            assert stored_user.role == UserRole.client
            profile = await db.scalar(
                select(Client).where(Client.user_id == stored_user.id)
            )
            assert profile is not None
            assert profile.first_name == "María Elena"
            assert profile.last_name == "Pérez"

        jwt = create_access_token(
            {"sub": body["id"], "role": UserRole.client.value}
        )
        client_me = await api_client.get(
            f"{API}/clients/me",
            headers={"Authorization": f"Bearer {jwt}"},
        )
        assert client_me.status_code == status.HTTP_200_OK, client_me.text
        assert client_me.json()["full_name"] == "María Elena Pérez"
        assert client_me.json()["email"] == email
    finally:
        await _cleanup_synthetic_account(email)


@pytest.mark.parametrize(
    "name", [None, "", "   ", "OnlyName", " X ", "  Ana   "]
)
async def test_client_signup_rejects_missing_or_incomplete_name_without_effect(
    api_client: httpx.AsyncClient,
    name: str | None,
) -> None:
    email = f"onboarding-invalid-{uuid.uuid4().hex}@example.com"
    payload = {"email": email, "password": "Only-Synthetic-Password-42"}
    if name is not None:
        payload["full_name"] = name
    response = await api_client.post(f"{API}/users/register-client", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User).where(User.email == email)) is None


@pytest.mark.parametrize("role", ["admin", "client", "teacher", "front_desk"])
async def test_client_signup_rejects_caller_role_even_client(
    api_client: httpx.AsyncClient,
    role: str,
) -> None:
    email = f"onboarding-role-{uuid.uuid4().hex}@example.com"
    response = await api_client.post(
        f"{API}/users/register-client",
        json={
            "email": email,
            "password": "Only-Synthetic-Password-42",
            "full_name": "Safe Client",
            "role": role,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User).where(User.email == email)) is None


async def test_client_signup_duplicate_email_has_no_extra_profile(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"onboarding-duplicate-{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "Only-Synthetic-Password-42",
        "full_name": "Safe Client",
    }
    try:
        first = await api_client.post(f"{API}/users/register-client", json=payload)
        assert first.status_code == status.HTTP_201_CREATED, first.text
        duplicate = await api_client.post(f"{API}/users/register-client", json=payload)
        assert duplicate.status_code == status.HTTP_400_BAD_REQUEST, duplicate.text

        async with AsyncSessionLocal() as db:
            users = (await db.scalars(select(User).where(User.email == email))).all()
            assert len(users) == 1
            profiles = (await db.scalars(
                select(Client).where(Client.user_id == users[0].id)
            )).all()
            assert len(profiles) == 1
    finally:
        await _cleanup_synthetic_account(email)


async def test_normalized_name_uses_post_normalization_length(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"onboarding-normalized-{uuid.uuid4().hex}@example.com"
    raw_name = (" " * 220) + "Ana Cliente" + (" " * 20)
    try:
        response = await api_client.post(
            f"{API}/users/register-client",
            json={
                "email": email,
                "password": "Only-Synthetic-Password-42",
                "full_name": raw_name,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        async with AsyncSessionLocal() as db:
            profile = await db.scalar(
                select(Client).join(Client.user).where(User.email == email)
            )
            assert profile is not None
            assert profile.first_name == "Ana"
            assert profile.last_name == "Cliente"
    finally:
        await _cleanup_synthetic_account(email)


async def test_normalized_name_over_limit_is_rejected_without_effect(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"onboarding-long-{uuid.uuid4().hex}@example.com"
    response = await api_client.post(
        f"{API}/users/register-client",
        json={
            "email": email,
            "password": "Only-Synthetic-Password-42",
            "full_name": "Ana " + ("X" * 201),
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User).where(User.email == email)) is None


async def test_two_simultaneous_http_signups_share_one_unique_account(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both callers pass the same precheck before racing on PostgreSQL UNIQUE."""
    email = f"onboarding-race-{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "Only-Synthetic-Password-42",
        "full_name": "Concurrent Client",
    }
    original_lookup = users_router.user_crud.get_by_email
    barrier = asyncio.Barrier(2)

    async def simultaneous_precheck(
        *,
        db: AsyncSession,
        email: str,
        include_deleted: bool = False,
        include_relations: bool = False,
    ) -> User | None:
        found = await original_lookup(
            db=db, email=email,
            include_deleted=include_deleted,
            include_relations=include_relations,
        )
        assert found is None
        await asyncio.wait_for(barrier.wait(), timeout=15)
        return None

    monkeypatch.setattr(users_router.user_crud, "get_by_email", simultaneous_precheck)
    try:
        responses = await asyncio.wait_for(
            asyncio.gather(
                api_client.post(f"{API}/users/register-client", json=payload),
                api_client.post(f"{API}/users/register-client", json=payload),
            ),
            timeout=30,
        )
        assert sorted(response.status_code for response in responses) == [201, 400]
        async with AsyncSessionLocal() as db:
            users = (await db.scalars(select(User).where(User.email == email))).all()
            assert len(users) == 1
            clients = (await db.scalars(
                select(Client).where(Client.user_id == users[0].id)
            )).all()
            assert len(clients) == 1
    finally:
        await _cleanup_synthetic_account(email)


async def test_db_failure_rolls_back_account_when_person_insert_fails(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inject a NOT NULL failure in Person after staging a new User."""
    email = f"onboarding-rollback-{uuid.uuid4().hex}@example.com"
    original = signup_service.Client

    def broken_profile(*, first_name: str, last_name: str, user: User) -> Client:
        return original(first_name=first_name, last_name=None, user=user)

    monkeypatch.setattr(signup_service, "Client", broken_profile)
    response = await api_client.post(
        f"{API}/users/register-client",
        json={
            "email": email,
            "password": "Only-Synthetic-Password-42",
            "full_name": "Atomic Failure",
        },
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User).where(User.email == email)) is None

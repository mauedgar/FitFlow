"""Security P0: real HTTP auth boundaries with only disposable test DB fixtures.

Exercise routing, signed JWT guards and mutations, not direct handler calls.
Never point these tests at retained staging or production data.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from dataclasses import dataclass

import httpx
import pytest
from fastapi import status
from sqlalchemy import delete, func, select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from app.core.security import create_access_token
from app.db.models import GymClass, User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]
API = settings.API_V1_STR


@dataclass(frozen=True)
class SecurityActors:
    marker: str
    class_id: uuid.UUID
    class_name: str
    admin_user_id: uuid.UUID
    tokens: dict[str, str]

    def headers(self, role: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens[role]}"}


@pytest.fixture(autouse=True)
def require_disposable_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test", (
        "Security HTTP contract may use only fitflow_test"
    )


@pytest.fixture(autouse=True)
async def dispose_async_pool_between_tests() -> AsyncIterator[None]:
    """Never reuse an asyncpg connection bound to another pytest event loop."""
    yield
    await engine.dispose()


@pytest.fixture
async def actors() -> AsyncIterator[SecurityActors]:
    marker = uuid.uuid4().hex
    class_name = f"P0 Audit {marker}"
    users = [
        User(
            email=f"p0-{marker}-{role.value}@example.com",
            hashed_password="synthetic-no-login",
            role=role,
        )
        for role in (UserRole.admin, UserRole.client, UserRole.teacher, UserRole.front_desk)
    ]
    inactive = User(
        email=f"p0-{marker}-inactive@example.com",
        hashed_password="synthetic-no-login",
        role=UserRole.client,
        active=False,
    )
    gym_class = GymClass(
        name=class_name,
        description="Disposable security route fixture",
        activity_type=ActivityType.group_class,
        duration_minutes=60,
        default_capacity=8,
    )
    async with AsyncSessionLocal() as db:
        db.add_all([*users, inactive, gym_class])
        await db.commit()
    identities = {user.role.value: user.id for user in users}
    tokens = {
        name: create_access_token({"sub": str(user_id), "role": name})
        for name, user_id in identities.items()
    }
    tokens["inactive"] = create_access_token(
        {"sub": str(inactive.id), "role": "client"}
    )
    tokens["forged_admin"] = create_access_token(
        {"sub": str(identities["client"]), "role": "admin"}
    )
    try:
        yield SecurityActors(
            marker=marker,
            class_id=gym_class.id,
            class_name=class_name,
            admin_user_id=identities["admin"],
            tokens=tokens,
        )
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(GymClass).where(GymClass.name.like(f"P0 Audit {marker}%"))
            )
            await db.execute(
                delete(User).where(User.email.like(f"p0-{marker}-%@example.com"))
            )
            await db.commit()


@pytest.mark.parametrize("supplied_role", ["admin", "teacher", "front_desk", "client"])
async def test_public_registration_rejects_any_role_and_creates_no_user(
    api_client: httpx.AsyncClient,
    supplied_role: str,
) -> None:
    email = f"p0-spoof-{uuid.uuid4().hex}@example.com"
    response = await api_client.post(
        f"{API}/users/register",
        json={
            "email": email,
            "password": "Synthetic-password-not-a-secret",
            "role": supplied_role,
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(User).where(User.email == email)) is None


async def test_public_registration_remains_client_only_and_accepts_legacy_full_name(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"p0-new-{uuid.uuid4().hex}@example.com"
    try:
        response = await api_client.post(
            f"{API}/users/register",
            json={
                "email": email,
                "password": "Synthetic-password-not-a-secret",
                "full_name": "Synthetic User",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        assert response.json()["role"] == "client"
        assert response.json()["email"] == email
        async with AsyncSessionLocal() as db:
            stored = await db.scalar(select(User).where(User.email == email))
            assert stored is not None
            assert stored.role == UserRole.client
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.email == email))
            await db.commit()


@pytest.mark.parametrize("path_kind", ["list", "detail"])
@pytest.mark.parametrize("actor", ["guest", "client", "teacher", "front_desk"])
async def test_user_identity_endpoints_deny_public_and_non_admin(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    path_kind: str,
    actor: str,
) -> None:
    path = (
        f"{API}/users/public"
        if path_kind == "list"
        else f"{API}/users/{actors.admin_user_id}/public"
    )
    response = await api_client.get(
        path,
        headers={} if actor == "guest" else actors.headers(actor),
    )
    expected = (
        status.HTTP_401_UNAUTHORIZED
        if actor == "guest"
        else status.HTTP_403_FORBIDDEN
    )
    assert response.status_code == expected, response.text
    assert "p0-" not in response.text


@pytest.mark.parametrize("path_kind", ["list", "detail"])
async def test_user_identity_endpoints_allow_admin(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    path_kind: str,
) -> None:
    path = (
        f"{API}/users/public"
        if path_kind == "list"
        else f"{API}/users/{actors.admin_user_id}/public"
    )
    response = await api_client.get(path, headers=actors.headers("admin"))
    assert response.status_code == status.HTTP_200_OK, response.text
    payload = response.json()
    if path_kind == "list":
        # The directory may be paginated and contain >100 pre-existing fixtures.
        assert isinstance(payload, list)
        assert all({"id", "email", "role", "active"} <= item.keys() for item in payload)
    else:
        assert payload["id"] == str(actors.admin_user_id)


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
@pytest.mark.parametrize("actor", ["guest", "client", "teacher", "front_desk"])
async def test_class_mutators_deny_unauthorized_without_side_effects(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    method: str,
    actor: str,
) -> None:
    path = (
        f"{API}/gym-classes/"
        if method == "POST"
        else f"{API}/gym-classes/{actors.class_id}"
    )
    payload = (
        {
            "name": f"P0 Audit {actors.marker} unauthorized",
            "description": "Must not persist",
            "duration_minutes": 60,
            "default_capacity": 8,
            "activity_type": "group_class",
        }
        if method == "POST"
        else {"name": f"P0 Audit {actors.marker} overwritten"}
        if method == "PUT"
        else None
    )
    response = await api_client.request(
        method,
        path,
        headers={} if actor == "guest" else actors.headers(actor),
        json=payload,
    )
    expected = status.HTTP_401_UNAUTHORIZED if actor == "guest" else status.HTTP_403_FORBIDDEN
    assert response.status_code == expected, response.text
    async with AsyncSessionLocal() as db:
        original = await db.scalar(select(GymClass).where(GymClass.id == actors.class_id))
        assert original is not None and original.name == actors.class_name
        count = await db.scalar(
            select(func.count()).select_from(GymClass).where(
                GymClass.name.like(f"P0 Audit {actors.marker}%")
            )
        )
        assert count == 1


async def test_admin_can_create_update_and_soft_delete_class(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    headers = actors.headers("admin")
    name = f"P0 Audit {actors.marker} admin-created"
    created = await api_client.post(
        f"{API}/gym-classes/",
        headers=headers,
        json={
            "name": name,
            "description": "Admin-only controlled creation",
            "duration_minutes": 60,
            "default_capacity": 8,
            "activity_type": "group_class",
        },
    )
    assert created.status_code == status.HTTP_201_CREATED, created.text
    new_id = created.json()["id"]
    edited = await api_client.put(
        f"{API}/gym-classes/{new_id}",
        headers=headers,
        json={"name": name + " updated"},
    )
    assert edited.status_code == status.HTTP_200_OK, edited.text
    assert edited.json()["name"] == name + " updated"
    removed = await api_client.delete(
        f"{API}/gym-classes/{new_id}",
        headers=headers,
    )
    assert removed.status_code == status.HTTP_202_ACCEPTED, removed.text


async def test_public_class_catalog_stays_accessible_without_credentials(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(f"{API}/gym-classes/public")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert any(item["id"] == str(actors.class_id) for item in response.json())


async def test_identity_directory_rejects_invalid_and_expired_jwt(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    invalid = await api_client.get(
        f"{API}/users/public",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED
    expired = create_access_token(
        {"sub": str(actors.admin_user_id), "role": "admin"},
        expires_delta=timedelta(seconds=-1),
    )
    expired_response = await api_client.get(
        f"{API}/users/public",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert expired_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_admin_claim_in_jwt_cannot_override_persisted_client_role(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(
        f"{API}/users/public",
        headers=actors.headers("forged_admin"),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "p0-" not in response.text


async def test_inactive_user_is_denied_even_with_signed_token(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(
        f"{API}/users/public",
        headers=actors.headers("inactive"),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "p0-" not in response.text


async def test_auth_me_preserves_valid_admin_identity_and_rejects_invalid_token(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    valid = await api_client.get(
        f"{API}/auth/me",
        headers=actors.headers("admin"),
    )
    assert valid.status_code == status.HTTP_200_OK, valid.text
    assert valid.json()["id"] == str(actors.admin_user_id)
    invalid = await api_client.get(
        f"{API}/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED

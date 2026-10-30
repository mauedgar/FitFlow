"""Real database HTTP authorization contract for client profiles.

Uses the existing isolated fitflow_test PostgreSQL schema, actual JWT guards,
SQLAlchemy ORM mappings, and real FastAPI ASGI routing. No external credentials.
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models import Client, User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class ClientProfileFixture:
    owner_id: uuid.UUID
    profile_id: uuid.UUID
    neighbor_id: uuid.UUID
    deleted_id: uuid.UUID
    owner_email: str
    tokens: dict[str, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        f"Client profile HTTP contract requires fitflow_test; got {database_name!r}"
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def profile_fixture() -> ClientProfileFixture:
    marker = uuid.uuid4().hex
    owner_email = f"client-profile-owner-{marker}@example.com"
    owner = Client(
        first_name="Ana",
        last_name="Cliente",
        user=User(
            email=owner_email,
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    neighbor = Client(
        first_name="Otra",
        last_name="Persona",
        user=User(
            email=f"client-profile-neighbor-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    deleted = Client(
        first_name="Baja",
        last_name="Logica",
        deleted_at=datetime.now(timezone.utc),
        user=User(
            email=f"client-profile-deleted-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    admin = User(
        email=f"client-profile-admin-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.admin,
    )
    teacher = User(
        email=f"client-profile-teacher-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.teacher,
    )

    async with AsyncSessionLocal() as db:
        db.add_all([owner, neighbor, deleted, admin, teacher])
        await db.flush()
        owner_id = owner.user_id
        profile_id = owner.id
        neighbor_id = neighbor.id
        deleted_id = deleted.id
        actors = {
            "owner": owner.user_id,
            "neighbor": neighbor.user_id,
            "deleted": deleted.user_id,
            "admin": admin.id,
            "teacher": teacher.id,
        }
        await db.commit()

    tokens = {
        name: create_access_token({"sub": str(identity), "role": (
            UserRole.admin.value if name == "admin"
            else UserRole.teacher.value if name == "teacher"
            else UserRole.client.value
        )})
        for name, identity in actors.items()
    }
    return ClientProfileFixture(
        owner_id=owner_id,
        profile_id=profile_id,
        neighbor_id=neighbor_id,
        deleted_id=deleted_id,
        owner_email=owner_email,
        tokens=tokens,
    )


def headers(fixture: ClientProfileFixture, name: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[name]}"}


async def test_admin_list_real_orm_projection_and_soft_delete(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        params={"skip": 0, "limit": 1000},
        headers=headers(profile_fixture, "admin"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    items = {item["id"]: item for item in result.json()}
    profile = items[str(profile_fixture.profile_id)]
    assert profile["full_name"] == "Ana Cliente"
    assert profile["email"] == profile_fixture.owner_email
    assert profile["phone"] is None
    assert profile["created_at"]
    assert str(profile_fixture.deleted_id) not in items


@pytest.mark.parametrize("name", ["owner", "teacher"])
async def test_admin_list_rejects_unauthorized_roles(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        headers=headers(profile_fixture, name),
    )
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_client_me_real_jwt_and_orm(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, "owner"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    assert result.json()["id"] == str(profile_fixture.profile_id)
    assert result.json()["email"] == profile_fixture.owner_email


@pytest.mark.parametrize("name", ["admin", "teacher"])
async def test_client_me_rejects_other_roles(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, name),
    )
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_soft_deleted_profile_not_accessible_through_me(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, "deleted"),
    )
    assert result.status_code == status.HTTP_404_NOT_FOUND


async def test_client_cannot_read_or_update_neighbors_profile(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    base = f"{settings.API_V1_STR}/clients/{profile_fixture.neighbor_id}"
    get_result = await api_client.get(base, headers=headers(profile_fixture, "owner"))
    put_result = await api_client.put(
        base,
        json={"first_name": "No"},
        headers=headers(profile_fixture, "owner"),
    )
    assert get_result.status_code == status.HTTP_403_FORBIDDEN
    assert put_result.status_code == status.HTTP_403_FORBIDDEN

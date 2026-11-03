"""IR007 F12/F15/A16: real HTTP authorization on disposable PG15 only."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models.person import Person
from app.db.models.teacher import Teacher
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import delete
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def isolated_database_only() -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def reset_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def principals() -> AsyncIterator[tuple[dict[str, UUID], UUID]]:
    accounts = {role.value: uuid4() for role in UserRole}
    profile_id = uuid4()
    marker = uuid4().hex
    async with AsyncSessionLocal() as db:
        db.add_all([
            User(
                id=uid,
                email=f"ir007-{role}-{marker}@example.invalid",
                hashed_password="synthetic-no-login",
                active=True,
                role=UserRole(role),
            )
            for role, uid in accounts.items()
        ])
        await db.commit()
        db.add(Teacher(
            id=profile_id,
            first_name="Synthetic",
            last_name="Instructor",
            user_id=accounts["teacher"],
            active=True,
        ))
        await db.commit()
    try:
        yield accounts, profile_id
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Teacher).where(Teacher.id == profile_id))
            await db.execute(delete(Person).where(Person.id == profile_id))
            await db.execute(delete(User).where(User.id.in_(list(accounts.values()))))
            await db.commit()


def bearer(accounts: dict[str, UUID], role: str) -> dict[str, str]:
    token = create_access_token({"sub": str(accounts[role]), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("method", ["post", "put", "delete"])
async def test_gym_catalog_mutation_rejects_anonymous_and_clients(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
    method: str,
) -> None:
    accounts, _ = principals
    gym_id = uuid4()
    path = "/gym-classes/" if method == "post" else f"/gym-classes/{gym_id}"
    payload = {
        "name": "Synthetic IR007 class",
        "description": "Isolated negative test",
        "duration_minutes": 30,
        "difficulty": "beginner",
        "default_capacity": 4,
        "activity_type": "group_class",
    } if method == "post" else {"name": "Unauthorized update"}
    url = f"{settings.API_V1_STR}{path}"
    anonymous = await api_client.request(
        method.upper(), url, json=payload if method != "delete" else None,
    )
    assert anonymous.status_code == 401, anonymous.text
    client = await api_client.request(
        method.upper(), url,
        json=payload if method != "delete" else None,
        headers=bearer(accounts, "client"),
    )
    assert client.status_code == 403, client.text


async def test_teacher_self_can_read_private_profile_with_distinct_person_id(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
) -> None:
    accounts, profile_id = principals
    assert accounts["teacher"] != profile_id
    url = f"{settings.API_V1_STR}/teachers/{profile_id}"
    own = await api_client.get(url, headers=bearer(accounts, "teacher"))
    assert own.status_code == 200, own.text
    assert own.json()["id"] == str(profile_id)
    admin = await api_client.get(url, headers=bearer(accounts, "admin"))
    assert admin.status_code == 200, admin.text
    other = await api_client.get(url, headers=bearer(accounts, "client"))
    assert other.status_code == 403, other.text
    anon = await api_client.get(url)
    assert anon.status_code == 401, anon.text


async def test_teacher_cannot_modify_unowned_profile_or_spoof_id(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
) -> None:
    accounts, profile_id = principals
    own = await api_client.put(
        f"{settings.API_V1_STR}/teachers/{profile_id}",
        json={"bio": "Synthetic profile update"},
        headers=bearer(accounts, "teacher"),
    )
    assert own.status_code == 200, own.text
    assert own.json()["bio"] == "Synthetic profile update"
    other = await api_client.put(
        f"{settings.API_V1_STR}/teachers/{profile_id}",
        json={"bio": "Not authorized"},
        headers=bearer(accounts, "front_desk"),
    )
    assert other.status_code == 403, other.text


@pytest.mark.parametrize("suffix", [
    "sessions/{id}/public",
    "classes/{id}/public",
    "class-schedules/{id}/public",
    "day?date_query=2026-11-02",
    "range?date_from=2026-11-02&date_to=2026-11-02",
])
async def test_booking_level_activity_is_not_anonymous_or_client_enumerable(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
    suffix: str,
) -> None:
    accounts, _ = principals
    url = f"{settings.API_V1_STR}/bookings/" + suffix.replace("{id}", str(uuid4()))
    public = await api_client.get(url)
    assert public.status_code == 401, public.text
    client = await api_client.get(url, headers=bearer(accounts, "client"))
    assert client.status_code == 403, client.text

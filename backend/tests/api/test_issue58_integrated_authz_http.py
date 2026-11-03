"""IR007 F12/F15/A16: real HTTP authorization on disposable PG15 only."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import MembershipPlan, MembershipStatus, UserRole
from app.core.security import create_access_token
from app.db.models.client import Client
from app.db.models.membership import Membership
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
                email=f"ir007-{role}-{marker}@example.com",
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


async def test_ir008_teacher_private_directory_is_admin_only_and_public_safe(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
) -> None:
    accounts, profile_id = principals
    secret = f"PRIVATE-DOCUMENT-{uuid4().hex}"
    async with AsyncSessionLocal() as db:
        teacher = await db.get(Teacher, profile_id)
        assert teacher is not None
        teacher.cuil = secret
        teacher.document_number = secret
        teacher.medical_fit_url = f"https://example.com/private/{secret}"
        teacher.address = "TEST PRIVATE HOME"
        await db.commit()

    url = f"{settings.API_V1_STR}/teachers/"
    anonymous = await api_client.get(url)
    assert anonymous.status_code == 401, anonymous.text
    colleague = await api_client.get(url, headers=bearer(accounts, "teacher"))
    assert colleague.status_code == 403, colleague.text
    admin = await api_client.get(url, headers=bearer(accounts, "admin"))
    assert admin.status_code == 200, admin.text
    entry = next(item for item in admin.json() if item["id"] == str(profile_id))
    assert entry["cuil"] == secret
    assert entry["document_number"] == secret
    assert entry["medical_fit_url"].endswith(secret)

    public = await api_client.get(f"{settings.API_V1_STR}/teachers/public")
    assert public.status_code == 200, public.text
    row = next(item for item in public.json() if item["id"] == str(profile_id))
    for field in ("cuil", "document_number", "address", "medical_fit_url"):
        assert field not in row
    assert secret not in public.text


@pytest.mark.parametrize("path", [
    "/gym-classes/{id}",
    "/teachers/",
    "/memberships/client/{id}/public",
])
async def test_ir008_invalid_bearer_is_401_not_500(
    api_client: httpx.AsyncClient,
    path: str,
) -> None:
    url = f"{settings.API_V1_STR}" + path.replace("{id}", str(uuid4()))
    response = await api_client.get(
        url, headers={"Authorization": "Bearer malformed-ir008-token"},
    )
    assert response.status_code == 401, response.text
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_ir008_client_membership_history_owner_admin_only(
    api_client: httpx.AsyncClient,
    principals: tuple[dict[str, UUID], UUID],
) -> None:
    accounts, _ = principals
    owner_profile_id, membership_id = uuid4(), uuid4()
    foreign_profile_id, foreign_account_id = uuid4(), uuid4()
    marker = uuid4().hex
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=foreign_account_id,
            email=f"ir008-foreign-{marker}@example.com",
            hashed_password="synthetic", role=UserRole.client, active=True,
        ))
        db.add(Client(
            id=owner_profile_id, first_name="Owner", last_name="Client",
            user_id=accounts["client"],
        ))
        db.add(Client(
            id=foreign_profile_id, first_name="Foreign", last_name="Client",
            user_id=foreign_account_id,
        ))
        await db.commit()
        db.add(Membership(
            id=membership_id,
            client_id=owner_profile_id,
            plan=MembershipPlan.premium,
            status=MembershipStatus.active,
            start_date=datetime.now(UTC)-timedelta(days=1),
            end_date=datetime.now(UTC)+timedelta(days=15),
        ))
        await db.commit()
    try:
        target = f"{settings.API_V1_STR}/memberships/client/{owner_profile_id}/public"
        anon = await api_client.get(target)
        assert anon.status_code == 401, anon.text
        owner = await api_client.get(target, headers=bearer(accounts, "client"))
        assert owner.status_code == 200, owner.text
        assert any(row["id"] == str(membership_id) for row in owner.json())
        admin = await api_client.get(target, headers=bearer(accounts, "admin"))
        assert admin.status_code == 200, admin.text
        teacher = await api_client.get(target, headers=bearer(accounts, "teacher"))
        assert teacher.status_code == 403, teacher.text
        foreign_token = create_access_token({
            "sub": str(foreign_account_id), "role": UserRole.client.value,
        })
        foreign = await api_client.get(
            target, headers={"Authorization": f"Bearer {foreign_token}"},
        )
        assert foreign.status_code == 403, foreign.text
        wrong = await api_client.get(
            f"{settings.API_V1_STR}/memberships/client/{foreign_profile_id}/public",
            headers=bearer(accounts, "client"),
        )
        assert wrong.status_code == 403, wrong.text
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Membership).where(Membership.id == membership_id))
            await db.execute(delete(Client).where(
                Client.id.in_([owner_profile_id, foreign_profile_id]),
            ))
            await db.execute(delete(Person).where(
                Person.id.in_([owner_profile_id, foreign_profile_id]),
            ))
            await db.execute(delete(User).where(User.id == foreign_account_id))
            await db.commit()

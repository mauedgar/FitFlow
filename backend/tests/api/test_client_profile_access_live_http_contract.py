"""Real database HTTP authorization contract for client profiles.

Uses the existing isolated fitflow_test PostgreSQL schema, actual JWT guards,
SQLAlchemy ORM mappings, and real FastAPI ASGI routing. No external credentials.
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import (
    ActivityType, BookingStatus, ClassSessionStatus, MembershipPlan,
    MembershipStatus, UserRole,
)
from app.core.security import create_access_token
from app.db.models import (
    Booking, ClassSchedule, ClassSession, Client, GymClass, Membership, User,
)
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class ClientProfileFixture:
    owner_id: uuid.UUID
    profile_id: uuid.UUID
    neighbor_id: uuid.UUID
    deleted_id: uuid.UUID
    owner_email: str
    membership_id: uuid.UUID
    booking_id: uuid.UUID
    unprofiled_user_id: uuid.UUID
    deleted_user_profile_id: uuid.UUID
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
    unprofiled = User(
        email=f"client-profile-new-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    deleted_user_client = Client(
        first_name="Account",
        last_name="Deleted",
        user=User(
            email=f"client-profile-user-deleted-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
            deleted_at=datetime.now(timezone.utc),
        ),
    )
    start = datetime.now(timezone.utc) + timedelta(days=2)
    membership = Membership(
        client=owner,
        plan=MembershipPlan.premium,
        status=MembershipStatus.active,
        start_date=datetime.now(timezone.utc) - timedelta(days=3),
        end_date=datetime.now(timezone.utc) + timedelta(days=40),
    )
    gym_class = GymClass(
        name=f"Client Profile Class {marker}",
        description="Profile HTTP contract class",
        activity_type=ActivityType.open_gym,
        duration_minutes=60,
        default_capacity=10,
    )
    schedule = ClassSchedule(
        gym_class=gym_class,
        teacher=None,
        rrule="RRULE:FREQ=DAILY;COUNT=1",
        start_date=date.today(),
        start_time=time(10, 0),
        duration_minutes=60,
        capacity=10,
    )
    session = ClassSession(
        class_schedule=schedule,
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        capacity_snapshot=10,
        status=ClassSessionStatus.scheduled,
    )
    booking = Booking(client=owner, class_session=session, status=BookingStatus.confirmed)

    async with AsyncSessionLocal() as db:
        db.add_all([
            owner, neighbor, deleted, admin, teacher, unprofiled,
            deleted_user_client, membership, gym_class, schedule, session, booking,
        ])
        await db.flush()
        owner_id = owner.user_id
        profile_id = owner.id
        neighbor_id = neighbor.id
        deleted_id = deleted.id
        membership_id = membership.id
        booking_id = booking.id
        unprofiled_user_id = unprofiled.id
        deleted_user_profile_id = deleted_user_client.id
        actors = {
            "owner": owner.user_id,
            "neighbor": neighbor.user_id,
            "deleted": deleted.user_id,
            "admin": admin.id,
            "teacher": teacher.id,
            "deleted_user": deleted_user_client.user_id,
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
        membership_id=membership_id,
        booking_id=booking_id,
        unprofiled_user_id=unprofiled_user_id,
        deleted_user_profile_id=deleted_user_profile_id,
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


@pytest.mark.parametrize("path", [
    "/clients/me/bookings", "/clients/me/membership",
    "/clients/me/stats", "/clients/me/activity",
])
async def test_own_profile_with_real_membership_and_booking_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    path: str,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}{path}",
        headers=headers(profile_fixture, "owner"),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    body = response.json()
    assert body["id"] == str(profile_fixture.profile_id)
    if path.endswith("/membership"):
        assert body["membership"]["id"] == str(profile_fixture.membership_id)
        assert body["membership"]["is_active"] is True
        assert body["membership"]["is_expired"] is False
    if path.endswith("/bookings"):
        assert len(body["bookings"]) == 1
        assert body["bookings"][0]["id"] == str(profile_fixture.booking_id)
        assert body["bookings"][0]["gym_class_name"].startswith("Client Profile Class")
    if path.endswith("/stats"):
        assert body["total_bookings"] == 1
        assert len(body["upcoming_bookings"]) == 1
    if path.endswith("/activity"):
        assert len(body["upcoming_bookings"]) == 1


@pytest.mark.parametrize("name", ["owner", "admin"])
async def test_get_and_put_private_client_profile_with_real_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    url = f"{settings.API_V1_STR}/clients/{profile_fixture.profile_id}"
    get_result = await api_client.get(url, headers=headers(profile_fixture, name))
    assert get_result.status_code == status.HTTP_200_OK, get_result.text
    body = get_result.json()
    assert len(body["bookings"]) == 1
    assert body["bookings"][0]["gym_class_name"].startswith("Client Profile Class")
    assert body["membership"]["is_active"] is True

    put_result = await api_client.put(
        url, json={"first_name": "Renamed"},
        headers=headers(profile_fixture, name),
    )
    assert put_result.status_code == status.HTTP_200_OK, put_result.text
    assert put_result.json()["first_name"] == "Renamed"
    assert len(put_result.json()["bookings"]) == 1
    assert put_result.json()["membership"]["id"] == str(profile_fixture.membership_id)


async def test_admin_create_client_serializes_empty_real_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/clients/{profile_fixture.unprofiled_user_id}",
        json={"first_name": "New", "last_name": "Profile"},
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["first_name"] == "New"
    assert response.json()["bookings"] == []
    assert response.json()["membership"] is None


async def test_membership_client_projection_has_preloaded_user(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/memberships/{profile_fixture.membership_id}",
        headers=headers(profile_fixture, "admin"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    assert result.json()["client"]["email"] == profile_fixture.owner_email


@pytest.mark.parametrize("credential", ["absent", "invalid", "expired", "missing_user", "deleted_user"])
async def test_client_profile_authentication_failures_are_http_401(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    credential: str,
) -> None:
    if credential == "absent":
        request_headers = {}
    elif credential == "invalid":
        request_headers = {"Authorization": "Bearer this-is-not-a-jwt"}
    elif credential == "expired":
        request_headers = {"Authorization": "Bearer " + create_access_token(
            {"sub": str(profile_fixture.owner_id), "role": UserRole.client.value},
            expires_delta=timedelta(seconds=-1),
        )}
    elif credential == "deleted_user":
        request_headers = headers(profile_fixture, "deleted_user")
    else:
        request_headers = {"Authorization": "Bearer " + create_access_token(
            {"sub": str(uuid.uuid4()), "role": UserRole.client.value}
        )}
    response = await api_client.get(
        f"{settings.API_V1_STR}/clients/me", headers=request_headers,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_admin_list_ignores_soft_deleted_users(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        params={"limit": 1000},
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    ids = {item["id"] for item in response.json()}
    assert str(profile_fixture.deleted_user_profile_id) not in ids

"""HTTP contract for Front Desk fallback Booking creation."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

import httpx
import pytest
from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    AllowedPlan,
    BookingStatus,
    ClassSessionStatus,
    MembershipPlan,
    MembershipStatus,
    UserRole,
)
from app.core.security import create_access_token
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Teacher,
    User,
)
from app.db.session import AsyncSessionLocal, engine

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@dataclass(frozen=True)
class FallbackFixture:
    session_id: uuid.UUID
    client_id: uuid.UUID
    membership_id: uuid.UUID
    tokens: dict[UserRole, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Front Desk fallback Booking contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


async def _seed_fallback_fixture() -> FallbackFixture:
    marker = uuid.uuid4().hex

    admin_user = User(
        email=f"b3-admin-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.admin,
    )
    front_desk_user = User(
        email=f"b3-front-desk-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.front_desk,
    )
    client_caller = User(
        email=f"b3-client-caller-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    teacher_caller = User(
        email=f"b3-teacher-caller-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.teacher,
    )

    teacher = Teacher(
        first_name="Fallback",
        last_name="Teacher",
        user=User(
            email=f"b3-session-teacher-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        ),
    )
    gym_class = GymClass(
        name=f"Fallback class {marker}",
        description="Front Desk fallback Booking contract",
        activity_type=ActivityType.group_class,
        duration_minutes=60,
        default_capacity=1,
    )
    schedule = ClassSchedule(
        gym_class=gym_class,
        teacher=teacher,
        rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
        start_time=time(10, 0),
        duration_minutes=60,
        capacity=1,
        start_date=datetime.now(UTC).date(),
        allowed_plan=AllowedPlan.classes,
    )
    starts_at = datetime.now(UTC) + timedelta(days=2)
    class_session = ClassSession(
        class_schedule=schedule,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        capacity_snapshot=1,
        status=ClassSessionStatus.scheduled,
    )

    target_client = Client(
        first_name="Fallback",
        last_name="Target",
        document_number=f"B3-{marker}",
        user=User(
            email=f"b3-target-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    membership = Membership(
        client=target_client,
        plan=MembershipPlan.classes,
        status=MembershipStatus.active,
        end_date=datetime.now(UTC) + timedelta(days=30),
    )

    capacity_client = Client(
        first_name="Capacity",
        last_name="Occupant",
        document_number=f"B3-capacity-{marker}",
        user=User(
            email=f"b3-capacity-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                admin_user,
                front_desk_user,
                client_caller,
                teacher_caller,
                teacher,
                gym_class,
                schedule,
                class_session,
                target_client,
                membership,
                capacity_client,
            ]
        )
        await db.flush()

        db.add(
            Booking(
                client_id=capacity_client.id,
                class_session_id=class_session.id,
                status=BookingStatus.confirmed,
            )
        )
        await db.flush()

        fixture = FallbackFixture(
            session_id=class_session.id,
            client_id=target_client.id,
            membership_id=membership.id,
            tokens={
                UserRole.admin: create_access_token(
                    {"sub": str(admin_user.id), "role": UserRole.admin.value}
                ),
                UserRole.front_desk: create_access_token(
                    {
                        "sub": str(front_desk_user.id),
                        "role": UserRole.front_desk.value,
                    }
                ),
                UserRole.client: create_access_token(
                    {"sub": str(client_caller.id), "role": UserRole.client.value}
                ),
                UserRole.teacher: create_access_token(
                    {"sub": str(teacher_caller.id), "role": UserRole.teacher.value}
                ),
            },
        )
        await db.commit()

    return fixture


@pytest.fixture
async def fallback_fixture() -> FallbackFixture:
    return await _seed_fallback_fixture()


def _headers(fixture: FallbackFixture, role: UserRole) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[role]}"}


async def _post_fallback(
    api_client: httpx.AsyncClient,
    fixture: FallbackFixture,
    role: UserRole = UserRole.front_desk,
) -> httpx.Response:
    return await api_client.post(
        (
            f"{settings.API_V1_STR}/front-desk/sessions/{fixture.session_id}"
            f"/clients/{fixture.client_id}/booking"
        ),
        headers=_headers(fixture, role),
    )


async def _target_bookings(fixture: FallbackFixture) -> list[Booking]:
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(Booking).where(
                Booking.class_session_id == fixture.session_id,
                Booking.client_id == fixture.client_id,
            )
        )
        return list(rows.scalars().all())


@pytest.mark.parametrize("role", [UserRole.admin, UserRole.front_desk])
async def test_fallback_creates_ordinary_confirmed_booking_without_check_in(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
    role: UserRole,
) -> None:
    response = await _post_fallback(api_client, fallback_fixture, role)

    assert response.status_code == status.HTTP_200_OK, response.text
    payload = response.json()
    assert payload["created"] is True
    assert payload["booking"]["client_id"] == str(fallback_fixture.client_id)
    assert payload["booking"]["status"] == BookingStatus.confirmed.value

    bookings = await _target_bookings(fallback_fixture)
    assert len(bookings) == 1
    assert bookings[0].status == BookingStatus.confirmed
    assert bookings[0].checked_in_at is None

    async with AsyncSessionLocal() as db:
        used = await db.scalar(
            select(func.count(Booking.id)).where(
                Booking.class_session_id == fallback_fixture.session_id,
                Booking.status != BookingStatus.cancelled,
            )
        )
    assert used == 2


async def test_fallback_returns_existing_booking_without_duplicate(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        existing = Booking(
            client_id=fallback_fixture.client_id,
            class_session_id=fallback_fixture.session_id,
            status=BookingStatus.confirmed,
        )
        db.add(existing)
        await db.commit()
        existing_id = existing.id

    response = await _post_fallback(api_client, fallback_fixture)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["created"] is False
    assert response.json()["booking"]["id"] == str(existing_id)
    assert response.json()["booking"]["status"] == BookingStatus.confirmed.value
    assert len(await _target_bookings(fallback_fixture)) == 1


async def test_fallback_requires_active_membership(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        membership = await db.get(Membership, fallback_fixture.membership_id)
        assert membership is not None
        membership.status = MembershipStatus.expired
        await db.commit()

    response = await _post_fallback(api_client, fallback_fixture)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Necesitas una membresía activa para reservar."}
    assert await _target_bookings(fallback_fixture) == []


async def test_fallback_enforces_allowed_plan(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        membership = await db.get(Membership, fallback_fixture.membership_id)
        assert membership is not None
        membership.plan = MembershipPlan.gym_only
        await db.commit()

    response = await _post_fallback(api_client, fallback_fixture)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no permite reservar esta clase" in response.json()["detail"]
    assert await _target_bookings(fallback_fixture) == []


async def test_fallback_unknown_client_is_not_found(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    response = await api_client.post(
        (
            f"{settings.API_V1_STR}/front-desk/sessions/{fallback_fixture.session_id}"
            f"/clients/{uuid.uuid4()}/booking"
        ),
        headers=_headers(fallback_fixture, UserRole.front_desk),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Cliente no encontrado."}


@pytest.mark.parametrize("role", [UserRole.client, UserRole.teacher])
async def test_fallback_rejects_unauthorized_roles(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
    role: UserRole,
) -> None:
    response = await _post_fallback(api_client, fallback_fixture, role)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Este recurso requiere uno de los siguientes roles: admin, front_desk."
    }


async def test_fallback_requires_authentication(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/front-desk/sessions/{fallback_fixture.session_id}"
        f"/clients/{fallback_fixture.client_id}/booking"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_fallback_then_check_in_remains_explicit_second_transition(
    api_client: httpx.AsyncClient,
    fallback_fixture: FallbackFixture,
) -> None:
    fallback = await _post_fallback(api_client, fallback_fixture)
    assert fallback.status_code == status.HTTP_200_OK, fallback.text
    assert fallback.json()["created"] is True
    assert fallback.json()["booking"]["status"] == BookingStatus.confirmed.value

    booking_id = fallback.json()["booking"]["id"]
    check_in = await api_client.post(
        (
            f"{settings.API_V1_STR}/front-desk/sessions/{fallback_fixture.session_id}"
            f"/bookings/{booking_id}/check-in"
        ),
        headers=_headers(fallback_fixture, UserRole.front_desk),
    )

    assert check_in.status_code == status.HTTP_200_OK, check_in.text
    assert check_in.json()["status"] == BookingStatus.attended.value

    async with AsyncSessionLocal() as db:
        stored = await db.get(Booking, uuid.UUID(booking_id))
        assert stored is not None
        assert stored.status == BookingStatus.attended
        assert stored.checked_in_at is not None

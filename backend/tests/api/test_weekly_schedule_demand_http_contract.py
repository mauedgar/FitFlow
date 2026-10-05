"""HTTP contract for weekly schedule expected-demand visibility."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    UserRole,
)
from app.core.security import create_access_token
from app.core.timezone import LOCAL_TZ
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
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
class WeeklyDemandFixture:
    week_start: date
    start_boundary_session_id: uuid.UUID
    target_session_id: uuid.UUID
    open_session_id: uuid.UUID
    excluded_session_ids: set[uuid.UUID]
    schedule_id: uuid.UUID
    tokens: dict[UserRole, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Weekly demand contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


def _utc(local_dt: datetime) -> datetime:
    return local_dt.astimezone(UTC)


async def _seed_weekly_demand_fixture() -> WeeklyDemandFixture:
    marker = uuid.uuid4().hex
    week_start = datetime.now(LOCAL_TZ).date() + timedelta(days=8)
    local_start = datetime.combine(week_start, time.min, tzinfo=LOCAL_TZ)
    local_end = local_start + timedelta(days=7)

    auth_users = {
        role: User(
            email=f"a1-{role.value}-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=role,
        )
        for role in (
            UserRole.admin,
            UserRole.front_desk,
            UserRole.client,
            UserRole.teacher,
        )
    }

    teacher = Teacher(
        first_name="Weekly",
        last_name="Teacher",
        user=User(
            email=f"a1-session-teacher-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        ),
    )
    gym_class = GymClass(
        name=f"Weekly demand {marker}",
        description="A1 weekly expected-demand contract",
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
        start_date=week_start,
    )

    def session_at(
        local_starts_at: datetime,
        session_status: ClassSessionStatus,
        *,
        active: bool = True,
        deleted_at: datetime | None = None,
    ) -> ClassSession:
        starts_at = _utc(local_starts_at)
        return ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=1,
            status=session_status,
            active=active,
            deleted_at=deleted_at,
        )

    start_boundary = session_at(
        local_start,
        ClassSessionStatus.scheduled,
    )
    target = session_at(
        local_start + timedelta(days=1, hours=10),
        ClassSessionStatus.scheduled,
    )
    open_session = session_at(
        local_start + timedelta(days=2, hours=11),
        ClassSessionStatus.open,
    )
    cancelled = session_at(
        local_start + timedelta(days=3, hours=10),
        ClassSessionStatus.cancelled,
    )
    completed = session_at(
        local_start + timedelta(days=4, hours=10),
        ClassSessionStatus.completed,
    )
    closed = session_at(
        local_start + timedelta(days=5, hours=10),
        ClassSessionStatus.closed,
    )
    inactive = session_at(
        local_start + timedelta(days=5, hours=12),
        ClassSessionStatus.scheduled,
        active=False,
    )
    deleted = session_at(
        local_start + timedelta(days=6, hours=10),
        ClassSessionStatus.scheduled,
        deleted_at=datetime.now(UTC),
    )
    end_boundary = session_at(local_end, ClassSessionStatus.scheduled)

    booking_clients = [
        Client(
            first_name="Demand",
            last_name=f"Client{index}",
            document_number=f"A1-{marker}-{index}",
            user=User(
                email=f"a1-booking-client-{marker}-{index}@example.com",
                hashed_password="not-a-real-password",
                role=UserRole.client,
            ),
        )
        for index in range(3)
    ]

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                *auth_users.values(),
                teacher,
                gym_class,
                schedule,
                start_boundary,
                target,
                open_session,
                cancelled,
                completed,
                closed,
                inactive,
                deleted,
                end_boundary,
                *booking_clients,
            ]
        )
        await db.flush()

        db.add_all(
            [
                Booking(
                    client_id=booking_clients[0].id,
                    class_session_id=target.id,
                    status=BookingStatus.confirmed,
                ),
                Booking(
                    client_id=booking_clients[1].id,
                    class_session_id=target.id,
                    status=BookingStatus.confirmed,
                ),
                Booking(
                    client_id=booking_clients[2].id,
                    class_session_id=target.id,
                    status=BookingStatus.cancelled,
                ),
            ]
        )
        await db.flush()

        fixture = WeeklyDemandFixture(
            week_start=week_start,
            start_boundary_session_id=start_boundary.id,
            target_session_id=target.id,
            open_session_id=open_session.id,
            excluded_session_ids={
                cancelled.id,
                completed.id,
                closed.id,
                inactive.id,
                deleted.id,
                end_boundary.id,
            },
            schedule_id=schedule.id,
            tokens={
                role: create_access_token(
                    {"sub": str(user.id), "role": role.value}
                )
                for role, user in auth_users.items()
            },
        )
        await db.commit()

    return fixture


@pytest.fixture
async def weekly_demand_fixture() -> WeeklyDemandFixture:
    return await _seed_weekly_demand_fixture()


def _headers(fixture: WeeklyDemandFixture, role: UserRole) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[role]}"}


async def _get_week(
    api_client: httpx.AsyncClient,
    fixture: WeeklyDemandFixture,
    *,
    week_start: date | None = None,
    role: UserRole = UserRole.client,
) -> httpx.Response:
    return await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/weekly-demand",
        params={"week_start": (week_start or fixture.week_start).isoformat()},
        headers=_headers(fixture, role),
    )


@pytest.mark.parametrize(
    "role",
    [UserRole.client, UserRole.front_desk, UserRole.admin],
)
async def test_weekly_demand_allows_accepted_authenticated_roles(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
    role: UserRole,
) -> None:
    response = await _get_week(api_client, weekly_demand_fixture, role=role)

    assert response.status_code == status.HTTP_200_OK, response.text
    payload = response.json()
    assert payload["week_start"] == weekly_demand_fixture.week_start.isoformat()
    assert payload["week_end_exclusive"] == (
        weekly_demand_fixture.week_start + timedelta(days=7)
    ).isoformat()

    ids = {uuid.UUID(item["session_id"]) for item in payload["items"]}
    expected_ids = {
        weekly_demand_fixture.start_boundary_session_id,
        weekly_demand_fixture.target_session_id,
        weekly_demand_fixture.open_session_id,
    }
    assert expected_ids <= ids
    assert ids.isdisjoint(weekly_demand_fixture.excluded_session_ids)


async def test_weekly_demand_reports_factual_unclamped_booking_demand(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    response = await _get_week(api_client, weekly_demand_fixture)
    assert response.status_code == status.HTTP_200_OK, response.text

    target = next(
        item
        for item in response.json()["items"]
        if uuid.UUID(item["session_id"]) == weekly_demand_fixture.target_session_id
    )
    assert target["class_schedule_id"] == str(weekly_demand_fixture.schedule_id)
    assert target["status"] == ClassSessionStatus.scheduled.value
    assert target["active_booking_count"] == 2
    assert target["reference_capacity"] == 1
    assert target["booking_occupancy_ratio"] == 2.0
    assert target["activity_id"]
    assert target["activity_name"]
    assert target["activity_type"] == ActivityType.group_class.value


async def test_weekly_demand_empty_week_returns_200_with_empty_items(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    response = await _get_week(
        api_client,
        weekly_demand_fixture,
        week_start=weekly_demand_fixture.week_start + timedelta(days=21),
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["items"] == []


async def test_weekly_demand_excludes_historical_scheduled_session(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    now = datetime.now(UTC)
    historical_start = now - timedelta(hours=2)
    historical_week_start = historical_start.astimezone(LOCAL_TZ).date()

    async with AsyncSessionLocal() as db:
        historical = ClassSession(
            class_schedule_id=weekly_demand_fixture.schedule_id,
            starts_at=historical_start,
            ends_at=now - timedelta(hours=1),
            capacity_snapshot=1,
            status=ClassSessionStatus.scheduled,
        )
        db.add(historical)
        await db.flush()
        historical_id = historical.id
        await db.commit()

    response = await _get_week(
        api_client,
        weekly_demand_fixture,
        week_start=historical_week_start,
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    ids = {uuid.UUID(item["session_id"]) for item in response.json()["items"]}
    assert historical_id not in ids


async def test_weekly_demand_rejects_teacher(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    response = await _get_week(
        api_client,
        weekly_demand_fixture,
        role=UserRole.teacher,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": (
            "Este recurso requiere uno de los siguientes roles: "
            "admin, front_desk, client."
        )
    }


async def test_weekly_demand_requires_authentication(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/weekly-demand",
        params={"week_start": weekly_demand_fixture.week_start.isoformat()},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


async def test_weekly_demand_requires_valid_local_date(
    api_client: httpx.AsyncClient,
    weekly_demand_fixture: WeeklyDemandFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/weekly-demand",
        params={"week_start": "not-a-date"},
        headers=_headers(weekly_demand_fixture, UserRole.client),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

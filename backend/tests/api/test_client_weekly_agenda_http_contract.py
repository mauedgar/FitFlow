"""HTTP contract for the authenticated Client weekly agenda."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

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
from app.core.timezone import LOCAL_TZ
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
class ClientWeeklyAgendaFixture:
    week_start: date
    membership_id: uuid.UUID
    booked_session_id: uuid.UUID
    unbooked_session_id: uuid.UUID
    ineligible_session_id: uuid.UUID
    excluded_session_ids: set[uuid.UUID]
    tokens: dict[UserRole, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Client weekly agenda contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


def _utc(local_dt: datetime) -> datetime:
    return local_dt.astimezone(UTC)


async def _seed_fixture() -> ClientWeeklyAgendaFixture:
    marker = uuid.uuid4().hex
    week_start = datetime.now(LOCAL_TZ).date() + timedelta(days=8)
    local_start = datetime.combine(week_start, time.min, tzinfo=LOCAL_TZ)
    local_end = local_start + timedelta(days=7)

    client_user = User(
        email=f"a3-client-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    client = Client(
        first_name="Agenda",
        last_name="Client",
        document_number=f"A3-{marker}",
        user=client_user,
    )
    membership = Membership(
        client=client,
        plan=MembershipPlan.gym_only,
        status=MembershipStatus.active,
        start_date=_utc(local_start - timedelta(days=30)),
        end_date=_utc(local_end + timedelta(days=30)),
    )

    auth_users = {
        role: User(
            email=f"a3-{role.value}-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=role,
        )
        for role in (UserRole.admin, UserRole.teacher)
    }

    open_gym = GymClass(
        name=f"Open gym {marker}",
        description="Teacherless A3 open-gym agenda fixture",
        activity_type=ActivityType.open_gym,
        duration_minutes=60,
        default_capacity=1,
    )
    open_gym_schedule = ClassSchedule(
        gym_class=open_gym,
        teacher=None,
        rrule="RRULE:FREQ=DAILY",
        start_time=time(10, 0),
        duration_minutes=60,
        capacity=1,
        start_date=week_start,
        allowed_plan=AllowedPlan.gym_only,
    )

    teacher = Teacher(
        first_name="Agenda",
        last_name="Teacher",
        user=User(
            email=f"a3-session-teacher-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        ),
    )
    classes = GymClass(
        name=f"Classes {marker}",
        description="Ineligible A3 schedule",
        activity_type=ActivityType.group_class,
        duration_minutes=60,
        default_capacity=10,
    )
    classes_schedule = ClassSchedule(
        gym_class=classes,
        teacher=teacher,
        rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
        start_time=time(12, 0),
        duration_minutes=60,
        capacity=10,
        start_date=week_start,
        allowed_plan=AllowedPlan.classes,
    )

    def session_at(
        schedule: ClassSchedule,
        local_starts_at: datetime,
        session_status: ClassSessionStatus = ClassSessionStatus.scheduled,
    ) -> ClassSession:
        starts_at = _utc(local_starts_at)
        return ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=schedule.capacity,
            status=session_status,
        )

    booked = session_at(open_gym_schedule, local_start + timedelta(days=1, hours=10))
    unbooked = session_at(open_gym_schedule, local_start + timedelta(days=2, hours=10))
    ineligible = session_at(classes_schedule, local_start + timedelta(days=3, hours=12))
    cancelled = session_at(
        open_gym_schedule,
        local_start + timedelta(days=4, hours=10),
        ClassSessionStatus.cancelled,
    )
    end_boundary = session_at(open_gym_schedule, local_end)

    other_client = Client(
        first_name="Demand",
        last_name="Other",
        document_number=f"A3-OTHER-{marker}",
        user=User(
            email=f"a3-other-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                client,
                membership,
                *auth_users.values(),
                open_gym,
                open_gym_schedule,
                teacher,
                classes,
                classes_schedule,
                booked,
                unbooked,
                ineligible,
                cancelled,
                end_boundary,
                other_client,
            ]
        )
        await db.flush()

        db.add_all(
            [
                Booking(
                    client_id=client.id,
                    class_session_id=booked.id,
                    status=BookingStatus.confirmed,
                ),
                Booking(
                    client_id=other_client.id,
                    class_session_id=booked.id,
                    status=BookingStatus.confirmed,
                ),
                Booking(
                    client_id=client.id,
                    class_session_id=unbooked.id,
                    status=BookingStatus.cancelled,
                ),
            ]
        )
        await db.flush()

        fixture = ClientWeeklyAgendaFixture(
            week_start=week_start,
            membership_id=membership.id,
            booked_session_id=booked.id,
            unbooked_session_id=unbooked.id,
            ineligible_session_id=ineligible.id,
            excluded_session_ids={cancelled.id, end_boundary.id},
            tokens={
                UserRole.client: create_access_token(
                    {"sub": str(client_user.id), "role": UserRole.client.value}
                ),
                **{
                    role: create_access_token(
                        {"sub": str(user.id), "role": role.value}
                    )
                    for role, user in auth_users.items()
                },
            },
        )
        await db.commit()

    return fixture


@pytest.fixture
async def agenda_fixture() -> ClientWeeklyAgendaFixture:
    return await _seed_fixture()


def _headers(fixture: ClientWeeklyAgendaFixture, role: UserRole) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[role]}"}


async def _get_agenda(
    api_client: httpx.AsyncClient,
    fixture: ClientWeeklyAgendaFixture,
    *,
    role: UserRole = UserRole.client,
) -> httpx.Response:
    return await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/weekly-agenda",
        params={"week_start": fixture.week_start.isoformat()},
        headers=_headers(fixture, role),
    )


async def test_client_weekly_agenda_composes_eligibility_booking_and_a1_demand(
    api_client: httpx.AsyncClient,
    agenda_fixture: ClientWeeklyAgendaFixture,
) -> None:
    response = await _get_agenda(api_client, agenda_fixture)
    assert response.status_code == status.HTTP_200_OK, response.text

    payload = response.json()
    assert payload["week_start"] == agenda_fixture.week_start.isoformat()
    assert payload["week_end_exclusive"] == (
        agenda_fixture.week_start + timedelta(days=7)
    ).isoformat()

    by_id = {uuid.UUID(item["session_id"]): item for item in payload["items"]}
    assert agenda_fixture.booked_session_id in by_id
    assert agenda_fixture.unbooked_session_id in by_id
    assert agenda_fixture.ineligible_session_id not in by_id
    assert set(by_id).isdisjoint(agenda_fixture.excluded_session_ids)

    booked = by_id[agenda_fixture.booked_session_id]
    assert booked["activity_type"] == ActivityType.open_gym.value
    assert booked["membership_plan_eligible"] is True
    assert booked["own_booking"]["status"] == BookingStatus.confirmed.value
    assert booked["active_booking_count"] == 2
    assert booked["reference_capacity"] == 1
    assert booked["booking_occupancy_ratio"] == 2.0

    unbooked = by_id[agenda_fixture.unbooked_session_id]
    assert unbooked["membership_plan_eligible"] is True
    assert unbooked["own_booking"] is None


async def test_client_weekly_agenda_is_client_only(
    api_client: httpx.AsyncClient,
    agenda_fixture: ClientWeeklyAgendaFixture,
) -> None:
    for role in (UserRole.admin, UserRole.teacher):
        response = await _get_agenda(api_client, agenda_fixture, role=role)
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_client_weekly_agenda_requires_active_membership(
    api_client: httpx.AsyncClient,
    agenda_fixture: ClientWeeklyAgendaFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        membership = await db.get(Membership, agenda_fixture.membership_id)
        assert membership is not None
        membership.status = MembershipStatus.paused
        await db.commit()

    response = await _get_agenda(api_client, agenda_fixture)
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["items"] == []


async def test_client_weekly_agenda_get_has_no_booking_write_effect(
    api_client: httpx.AsyncClient,
    agenda_fixture: ClientWeeklyAgendaFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        before = await db.scalar(select(func.count()).select_from(Booking))

    response = await _get_agenda(api_client, agenda_fixture)
    assert response.status_code == status.HTTP_200_OK, response.text

    async with AsyncSessionLocal() as db:
        after = await db.scalar(select(func.count()).select_from(Booking))

    assert after == before


async def test_client_weekly_agenda_requires_authentication(
    api_client: httpx.AsyncClient,
    agenda_fixture: ClientWeeklyAgendaFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/weekly-agenda",
        params={"week_start": agenda_fixture.week_start.isoformat()},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

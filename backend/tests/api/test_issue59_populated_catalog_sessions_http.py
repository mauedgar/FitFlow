"""IR008 F19/F20: real populated ORM relationships and UUID filter boundaries.

Only disposable fitflow_test PG15 is used. No production or staging credentials.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import ActivityType, ClassSessionStatus
from app.db.models.class_schedule import ClassSchedule
from app.db.models.class_session import ClassSession
from app.db.models.gym_class import GymClass
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import delete
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_postgresql() -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def catalog_session() -> AsyncIterator[tuple[UUID, UUID, UUID, UUID, date]]:
    class_id, schedule_id, session_id, cancelled_id = (
        uuid4(), uuid4(), uuid4(), uuid4()
    )
    start = datetime.combine(date.today() + timedelta(days=5), time(15, 0), tzinfo=UTC)
    async with AsyncSessionLocal() as db:
        klass = GymClass(
            id=class_id, name=f"IR008 Gym {uuid4().hex}",
            description="Populated category projection", activity_type=ActivityType.open_gym,
            duration_minutes=45, default_capacity=8, active=True,
        )
        schedule = ClassSchedule(
            id=schedule_id, gym_class=klass, teacher=None,
            rrule="RRULE:FREQ=WEEKLY;COUNT=2", start_date=start.date(),
            start_time=time(10, 0), duration_minutes=45, capacity=8, active=True,
            allowed_plan=None,
        )
        first = ClassSession(
            id=session_id, class_schedule=schedule, starts_at=start,
            ends_at=start + timedelta(minutes=45), capacity_snapshot=8,
            status=ClassSessionStatus.scheduled, active=True,
        )
        cancelled = ClassSession(
            id=cancelled_id, class_schedule=schedule,
            starts_at=start + timedelta(days=7),
            ends_at=start + timedelta(days=7, minutes=45),
            capacity_snapshot=8, status=ClassSessionStatus.cancelled, active=True,
        )
        db.add_all([klass, schedule, first, cancelled])
        await db.commit()
    try:
        yield class_id, schedule_id, session_id, cancelled_id, start.date()
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(ClassSession).where(
                ClassSession.id.in_([session_id, cancelled_id]),
            ))
            await db.execute(delete(ClassSchedule).where(ClassSchedule.id == schedule_id))
            await db.execute(delete(GymClass).where(GymClass.id == class_id))
            await db.commit()


async def test_ir008_public_class_session_filter_joins_gym_class_not_schedule_uuid(
    api_client: httpx.AsyncClient,
    catalog_session: tuple[UUID, UUID, UUID, UUID, date],
) -> None:
    class_id, schedule_id, session_id, _cancelled, _day = catalog_session
    assert class_id != schedule_id
    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/class/{class_id}/public",
    )
    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()}
    assert str(session_id) in ids

    wrong = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/class/{schedule_id}/public",
    )
    assert wrong.status_code == 200, wrong.text
    assert not any(item["id"] == str(session_id) for item in wrong.json())


async def test_ir008_schedule_date_and_cancelled_filters_are_live(
    api_client: httpx.AsyncClient,
    catalog_session: tuple[UUID, UUID, UUID, UUID, date],
) -> None:
    _class_id, schedule_id, session_id, cancelled_id, day = catalog_session
    params = {
        "schedule_id": str(schedule_id), "date_from": str(day - timedelta(days=1)),
        "date_to": str(day + timedelta(days=10)), "include_cancelled": False,
    }
    response = await api_client.get(f"{settings.API_V1_STR}/class-sessions/", params=params)
    assert response.status_code == 200, response.text
    ids = {row["id"] for row in response.json()}
    assert str(session_id) in ids
    assert str(cancelled_id) not in ids
    both = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/",
        params={**params, "include_cancelled": True},
    )
    assert both.status_code == 200, both.text
    assert str(cancelled_id) in {row["id"] for row in both.json()}

    unrelated = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/",
        params={**params, "schedule_id": str(uuid4())},
    )
    assert unrelated.status_code == 200, unrelated.text
    assert unrelated.json() == []


async def test_ir008_populated_operational_and_public_projections_are_200(
    api_client: httpx.AsyncClient,
    catalog_session: tuple[UUID, UUID, UUID, UUID, date],
) -> None:
    class_id, schedule_id, _sid, _cancelled, _date = catalog_session
    schedules = await api_client.get(
        f"{settings.API_V1_STR}/class-schedules/",
        params={"gym_class_id": str(class_id), "include_relations": False},
    )
    assert schedules.status_code == 200, schedules.text
    row = next(row for row in schedules.json() if row["id"] == str(schedule_id))
    assert row["gym_class"]["id"] == str(class_id)
    assert row["teacher"] is None

    classes = await api_client.get(
        f"{settings.API_V1_STR}/gym-classes/",
        params={"search": "IR008 Gym", "include_schedules": True},
    )
    assert classes.status_code == 200, classes.text
    item = next(row for row in classes.json() if row["id"] == str(class_id))
    assert item["class_schedules"]
    assert item["class_schedules"][0]["id"] == str(schedule_id)
    assert item["class_schedules"][0]["allowed_plan"] is None
    assert item["class_schedules"][0]["teacher"] is None

    public = await api_client.get(f"{settings.API_V1_STR}/gym-classes/public")
    assert public.status_code == 200, public.text
    public_item = next(row for row in public.json() if row["id"] == str(class_id))
    assert "deleted_at" not in public_item
    assert "created_at" not in public_item


async def test_ir009_static_daily_route_precedes_dynamic_uuid_and_filters_date(
    api_client: httpx.AsyncClient,
    catalog_session: tuple[UUID, UUID, UUID, UUID, date],
) -> None:
    """F21: the mounted HTTP router must execute /day, not /{session_id}."""
    _gym_id, _schedule_id, session_id, _cancelled_id, day = catalog_session
    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/day",
        params={"date_query": day.isoformat()},
    )
    assert response.status_code == 200, response.text
    assert str(session_id) in {item["id"] for item in response.json()}
    malformed = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/day",
        params={"date_query": "invalid-date"},
    )
    assert malformed.status_code == 422, malformed.text

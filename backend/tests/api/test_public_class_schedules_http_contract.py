"""HTTP and loader contract for public ClassSchedule relation materialization."""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time

import httpx
import pytest
from fastapi import status
from sqlalchemy import event, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.exc import InvalidRequestError

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from app.crud.crud_class_schedule import class_schedule as class_schedule_crud
from app.db.models import ClassSchedule, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    """Dispose pooled DB connections after each public schedule contract test."""
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    """Fail closed unless the HTTP contract uses the isolated test database."""
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Public class schedules HTTP contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _public_schedule_fixture(
    schedule_count: int = 1,
) -> tuple[uuid.UUID, list[uuid.UUID], uuid.UUID]:
    """Create real public schedules sharing one gym_class and teacher."""
    token = uuid.uuid4().hex

    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"public-schedule-teacher-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="Public",
            last_name="Schedule",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"Public schedule {token}",
            description="Public schedule relation loading contract",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=12,
        )
        schedules = [
            ClassSchedule(
                gym_class=gym_class,
                teacher=teacher,
                rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
                start_time=time(18, 30 + index),
                duration_minutes=60,
                capacity=12,
                start_date=datetime.now(UTC).date(),
            )
            for index in range(schedule_count)
        ]

        db.add_all([teacher, gym_class, *schedules])
        await db.flush()

        class_id = gym_class.id
        schedule_ids = [schedule.id for schedule in schedules]
        teacher_id = teacher.id

        await db.commit()

    return class_id, schedule_ids, teacher_id


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route_kind",
    ["top_level", "class_filtered", "teacher_filtered", "gym_class_nested"],
)
async def test_registered_public_class_schedule_variants_materialize_required_relations(
    api_client: httpx.AsyncClient,
    route_kind: str,
) -> None:
    """Every registered ClassSchedulePublic list variant returns nested relations."""
    class_id, schedule_ids, teacher_id = await _public_schedule_fixture()
    schedule_id = schedule_ids[0]

    if route_kind == "top_level":
        path = f"{settings.API_V1_STR}/class-schedules/public?limit=1000"
    elif route_kind == "class_filtered":
        path = f"{settings.API_V1_STR}/class-schedules/class/{class_id}/public"
    elif route_kind == "teacher_filtered":
        path = f"{settings.API_V1_STR}/class-schedules/teacher/{teacher_id}/public"
    elif route_kind == "gym_class_nested":
        path = f"{settings.API_V1_STR}/gym-classes/{class_id}/schedules/public"
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(f"unknown route kind: {route_kind}")

    response = await api_client.get(path)
    assert response.status_code == status.HTTP_200_OK, response.text

    payload = response.json()
    matches = [item for item in payload if item["id"] == str(schedule_id)]
    assert len(matches) == 1, payload

    schedule = matches[0]
    assert schedule["duration_minutes"] == 60
    assert isinstance(schedule["duration_minutes"], int)
    assert schedule["gym_class"]["id"] == str(class_id)
    assert schedule["gym_class"]["name"].startswith("Public schedule ")
    assert schedule["teacher"]["id"] == str(teacher_id)
    assert schedule["teacher"]["first_name"] == "Public"
    assert schedule["teacher"]["last_name"] == "Schedule"


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_public_loader_is_explicit_without_class_sessions_and_has_bounded_query_count() -> None:
    """Prove exact loader state and a constant three-query multi-row SQL shape."""
    class_id, schedule_ids, _ = await _public_schedule_fixture(schedule_count=2)
    expected_ids = set(schedule_ids)
    query_count = 0

    def count_statement(*_: object) -> None:
        nonlocal query_count
        query_count += 1

    event.listen(engine.sync_engine, "before_cursor_execute", count_statement)
    try:
        async with AsyncSessionLocal() as db:
            schedules = await class_schedule_crud.get_multi_public(
                db=db,
                gym_class_id=class_id,
                active=True,
                limit=10,
            )

            assert {schedule.id for schedule in schedules} == expected_ids
            assert query_count == 3

            before_relation_access = query_count
            for schedule in schedules:
                state = inspect(schedule)
                assert "gym_class" not in state.unloaded
                assert "teacher" not in state.unloaded
                assert "class_sessions" in state.unloaded

                assert schedule.gym_class.id == class_id
                assert schedule.teacher.id is not None
                with pytest.raises(InvalidRequestError):
                    _ = schedule.class_sessions

            assert query_count == before_relation_access == 3
            print(
                "LOADER_EVIDENCE "
                "rows=2 query_count=3 "
                "gym_class_loaded=true teacher_loaded=true "
                "class_sessions_unloaded=true class_sessions_raiseload=true"
            )
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", count_statement)

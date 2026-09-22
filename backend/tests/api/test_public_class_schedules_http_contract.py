"""HTTP contract for public class schedules with required relation loading."""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from app.db.models import ClassSchedule, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    """Dispose pooled DB connections after the API integration test."""
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


async def _public_schedule_fixture() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Create one real public class schedule with gym_class and teacher relations."""
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
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
            start_time=time(18, 30),
            duration_minutes=60,
            capacity=12,
            start_date=datetime.now(UTC).date(),
        )

        db.add_all([teacher, gym_class, schedule])
        await db.flush()

        class_id = gym_class.id
        schedule_id = schedule.id
        teacher_id = teacher.id

        await db.commit()

    return class_id, schedule_id, teacher_id


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_public_class_schedules_materialize_required_relations(
    api_client: httpx.AsyncClient,
) -> None:
    """Require HTTP 200 and nested ClassSchedulePublic relation serialization."""
    class_id, schedule_id, teacher_id = await _public_schedule_fixture()

    response = await api_client.get(
        f"{settings.API_V1_STR}/gym-classes/{class_id}/schedules/public"
    )

    assert response.status_code == status.HTTP_200_OK, response.text

    payload = response.json()
    assert len(payload) == 1, payload

    schedule = payload[0]
    assert schedule["id"] == str(schedule_id)
    assert schedule["duration_minutes"] == 60
    assert isinstance(schedule["duration_minutes"], int)

    assert schedule["gym_class"]["id"] == str(class_id)
    assert schedule["gym_class"]["name"].startswith("Public schedule ")

    assert schedule["teacher"]["id"] == str(teacher_id)
    assert schedule["teacher"]["first_name"] == "Public"
    assert schedule["teacher"]["last_name"] == "Schedule"
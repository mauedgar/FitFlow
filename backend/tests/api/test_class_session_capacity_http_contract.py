"""HTTP contract for ClassSession availability capacity snapshots."""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time, timedelta

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, ClassSessionStatus, UserRole
from app.db.models import ClassSchedule, ClassSession, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    """Dispose pooled DB connections after this integration test."""
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    """Fail closed unless this contract test uses fitflow_test."""
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "ClassSession HTTP capacity contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _session_with_snapshot() -> tuple[uuid.UUID, int]:
    """Create a real session whose snapshot differs from schedule capacity."""
    token = uuid.uuid4().hex
    snapshot_capacity = 3

    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"class-session-capacity-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="Capacity",
            last_name="Contract",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"ClassSession capacity {token}",
            description="ClassSession capacity HTTP contract",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=9,
        )
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
            start_time=time(12, 0),
            duration_minutes=60,
            capacity=9,
            start_date=datetime.now(UTC).date(),
        )
        starts_at = datetime.now(UTC) + timedelta(days=2)
        class_session = ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=snapshot_capacity,
            status=ClassSessionStatus.scheduled,
        )

        db.add_all([teacher, gym_class, schedule, class_session])
        await db.flush()
        session_id = class_session.id
        await db.commit()

    return session_id, snapshot_capacity


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_availability_capacity_uses_session_snapshot(
    api_client: httpx.AsyncClient,
) -> None:
    """Prove ClassSession availability preserves per-session capacity."""
    session_id, snapshot_capacity = await _session_with_snapshot()

    response = await api_client.get(
        f"{settings.API_V1_STR}/class-sessions/{session_id}/availability"
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {
        "session_id": str(session_id),
        "capacity": snapshot_capacity,
        "used": 0,
        "available": snapshot_capacity,
    }
"""Minimal real Booking HTTP vertical over session capacity."""

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
    """Dispose pooled DB connections after the API integration test."""
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    """Fail closed unless the API vertical uses the isolated test database."""
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Booking HTTP vertical requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _session_with_snapshot() -> tuple[uuid.UUID, int]:
    """Create a real session whose snapshot differs from its schedule capacity."""
    token = uuid.uuid4().hex
    snapshot_capacity = 3

    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"http-vertical-teacher-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="HTTP",
            last_name="Vertical",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"HTTP vertical {token}",
            description="Booking capacity HTTP vertical",
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
async def test_can_book_capacity_uses_session_snapshot(
    api_client: httpx.AsyncClient,
) -> None:
    """Prove the Booking capacity endpoint preserves the session snapshot."""
    session_id, snapshot_capacity = await _session_with_snapshot()

    response = await api_client.get(
        f"{settings.API_V1_STR}/bookings/sessions/{session_id}/can-book"
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {
        "session_id": str(session_id),
        "capacity": snapshot_capacity,
        "used": 0,
        "available": snapshot_capacity,
    }
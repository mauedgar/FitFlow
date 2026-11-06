"""Real PostgreSQL negative cases for the R006 reserved-fixture ownership guard."""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from app.db.models import Booking, ClassSchedule, ClassSession, Client, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine
from scripts.staging_smoke_seed import (
    CLIENT_EMAIL, CLIENT_ID, CLIENT_USER_ID, assert_fixture_ownership,
)


@pytest.fixture(autouse=True)
def require_disposable_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def release_pool_after_test():
    yield
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_reserved_user_collision_refused_and_rolled_back() -> None:
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=CLIENT_USER_ID, email=f"unrelated-{uuid.uuid4()}@example.test",
            hashed_password="synthetic-only", role=UserRole.client,
        ))
        await db.flush()
        with pytest.raises(RuntimeError, match="Unowned user/email"):
            await assert_fixture_ownership(db)
        await db.rollback()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sql_unrelated_booking_with_reserved_client_is_refused_and_rolled_back() -> None:
    async with AsyncSessionLocal() as db:
        client = Client(
            id=CLIENT_ID, first_name="Wave B", last_name="Client",
            document_number="M4-WAVE-B-SMOKE-CLIENT",
            user=User(
                id=CLIENT_USER_ID, email=CLIENT_EMAIL,
                hashed_password="synthetic-only", role=UserRole.client,
            ),
        )
        teacher = Teacher(
            first_name="Unrelated", last_name="Synthetic",
            user=User(
                email=f"unrelated-teacher-{uuid.uuid4()}@example.test",
                hashed_password="synthetic-only", role=UserRole.teacher,
            ),
        )
        gym_class = GymClass(
            name=f"Other test class {uuid.uuid4()}", description="Isolation regression",
            activity_type=ActivityType.group_class, duration_minutes=45,
            default_capacity=5,
        )
        schedule = ClassSchedule(
            gym_class=gym_class, teacher=teacher, rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(10, 0), duration_minutes=45, capacity=5,
            start_date=date.today(),
        )
        start = datetime.now(UTC) + timedelta(days=1)
        session = ClassSession(
            class_schedule=schedule, starts_at=start,
            ends_at=start + timedelta(minutes=45), capacity_snapshot=5,
        )
        booking = Booking(client=client, class_session=session)
        db.add_all([client, teacher, gym_class, schedule, session, booking])
        await db.flush()
        with pytest.raises(RuntimeError, match="Unowned booking"):
            await assert_fixture_ownership(db)
        await db.rollback()

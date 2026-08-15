"""Integration coverage for RRULE-only session generation."""

import uuid
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, ClassSessionStatus, UserRole
from app.db.models import ClassSchedule, ClassSession, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine
from app.services import errors as svc_errors
from app.services.class_schedule_service import generate_sessions_for_schedule


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test():
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generation_is_idempotent_and_preserves_schedule_snapshot() -> None:
    start_date = datetime.now(UTC).date() + timedelta(days=1)
    async with AsyncSessionLocal() as db:
        teacher = Teacher(
            first_name="RRULE",
            last_name="Teacher",
            document_number=str(uuid.uuid4()),
            user=User(
                email=f"rrule-teacher-{uuid.uuid4()}@example.test",
                hashed_password="not-a-real-password",
                role=UserRole.teacher,
            ),
        )
        gym_class = GymClass(
            name=f"RRULE class {uuid.uuid4()}",
            description="RRULE integration class",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=7,
        )
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=DAILY;COUNT=3",
            start_time=time(9, 0),
            duration_minutes=60,
            capacity=7,
            start_date=start_date,
        )
        db.add(schedule)
        await db.commit()

        generated = await generate_sessions_for_schedule(
            str(schedule.id), start_date, start_date + timedelta(days=15), None, db=db
        )
        repeated = await generate_sessions_for_schedule(
            str(schedule.id), start_date, start_date + timedelta(days=15), None, db=db
        )
        stored = list(
            (
                await db.scalars(
                    select(ClassSession)
                    .where(ClassSession.class_schedule_id == schedule.id)
                    .order_by(ClassSession.starts_at)
                )
            ).all()
        )

    assert len(generated) == 3
    assert repeated == []
    assert len(stored) == 3
    assert all(item.status is ClassSessionStatus.scheduled for item in stored)
    assert all(item.capacity_snapshot == 7 for item in stored)
    assert all(item.ends_at - item.starts_at == timedelta(minutes=60) for item in stored)
    assert [item.starts_at.date() for item in stored] == [
        start_date,
        start_date + timedelta(days=1),
        start_date + timedelta(days=2),
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generation_rejects_active_teacher_overlap() -> None:
    start_date = datetime.now(UTC).date() + timedelta(days=1)
    async with AsyncSessionLocal() as db:
        teacher = Teacher(
            first_name="Overlap",
            last_name="Teacher",
            document_number=str(uuid.uuid4()),
            user=User(
                email=f"overlap-teacher-{uuid.uuid4()}@example.test",
                hashed_password="not-a-real-password",
                role=UserRole.teacher,
            ),
        )
        gym_class = GymClass(
            name=f"Overlap class {uuid.uuid4()}",
            description="Overlap integration class",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=8,
        )
        first = ClassSchedule(
            gym_class=gym_class, teacher=teacher, rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(9), duration_minutes=60, capacity=8, start_date=start_date,
        )
        second = ClassSchedule(
            gym_class=gym_class, teacher=teacher, rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(9, 30), duration_minutes=60, capacity=8, start_date=start_date,
        )
        db.add_all([first, second])
        await db.commit()
        await generate_sessions_for_schedule(str(first.id), start_date, start_date, None, db=db)
        with pytest.raises(svc_errors.BusinessValidationError, match="Solapamiento"):
            await generate_sessions_for_schedule(str(second.id), start_date, start_date, None, db=db)

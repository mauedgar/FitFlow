"""A2 contract: open-gym schedules may be teacherless, directed activities may not."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time, timedelta

import pytest
from fastapi import HTTPException, status
from sqlalchemy import inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from app.crud.crud_class_schedule import class_schedule as class_schedule_crud
from app.db.models import ClassSchedule, ClassSession, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine
from app.routers.class_schedules import create_class_schedule, update_class_schedule
from app.schemas.class_schedule import ClassScheduleCreate, ClassScheduleUpdate
from app.services import class_schedule_service
from app.services.class_schedule_service import to_class_schedule_public
from app.services.front_desk_service import to_frontdesk_session_view

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


def _admin_user(marker: str) -> User:
    return User(
        email=f"a2-admin-{marker}@example.test",
        hashed_password="not-a-real-password",
        role=UserRole.admin,
    )


def _teacher(marker: str) -> Teacher:
    return Teacher(
        first_name="A2",
        last_name="Teacher",
        document_number=str(uuid.uuid4()),
        user=User(
            email=f"a2-teacher-{marker}@example.test",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        ),
    )


def _gym_class(marker: str, activity_type: ActivityType) -> GymClass:
    return GymClass(
        name=f"A2 {activity_type.value} {marker}",
        description="A2 optional open-gym Teacher contract",
        activity_type=activity_type,
        duration_minutes=60,
        default_capacity=8,
    )


def _schedule_create(
    gym_class_id: uuid.UUID,
    *,
    teacher_id: uuid.UUID | None,
    start_date: date,
    start_hour: int = 9,
) -> ClassScheduleCreate:
    return ClassScheduleCreate(
        gym_class_id=gym_class_id,
        teacher_id=teacher_id,
        rrule="RRULE:FREQ=DAILY;COUNT=1",
        start_time=time(start_hour, 0),
        duration_minutes=60,
        capacity=8,
        start_date=start_date,
    )


async def test_migration_exposes_nullable_teacher_id() -> None:
    async with engine.connect() as conn:
        nullable = await conn.run_sync(
            lambda sync_conn: next(
                column["nullable"]
                for column in inspect(sync_conn).get_columns("class_schedules")
                if column["name"] == "teacher_id"
            )
        )

    assert nullable is True


async def test_teacherless_open_gym_create_generation_and_projections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = uuid.uuid4().hex
    start_date = datetime.now(UTC).date() + timedelta(days=1)

    async def fail_if_teacher_conflict_is_checked(*args: object, **kwargs: object) -> bool:
        del args, kwargs
        raise AssertionError("teacher conflict lookup must be skipped without Teacher")

    monkeypatch.setattr(
        class_schedule_service.crud_class_session,
        "teacher_has_conflict",
        fail_if_teacher_conflict_is_checked,
    )

    async with AsyncSessionLocal() as db:
        admin = _admin_user(marker)
        open_gym = _gym_class(marker, ActivityType.open_gym)
        db.add_all([admin, open_gym])
        await db.commit()

        created = await create_class_schedule(
            db=db,
            schedule_in=_schedule_create(
                open_gym.id,
                teacher_id=None,
                start_date=start_date,
            ),
            current_user=admin,  # type: ignore[arg-type]
        )

        assert created.teacher_id is None
        assert created.teacher is None

        schedule = await class_schedule_crud.get(
            db=db,
            obj_id=created.id,
            include_relations=True,
        )
        assert schedule is not None
        public = to_class_schedule_public(schedule)
        assert public.teacher is None

        session = (
            await db.execute(
                select(ClassSession)
                .where(ClassSession.class_schedule_id == created.id)
                .options(
                    selectinload(ClassSession.class_schedule).selectinload(
                        ClassSchedule.gym_class
                    ),
                    selectinload(ClassSession.class_schedule).selectinload(
                        ClassSchedule.teacher
                    ),
                    selectinload(ClassSession.bookings),
                )
            )
        ).scalar_one()
        front_desk = to_frontdesk_session_view(session)

    assert front_desk.teacher_id is None
    assert front_desk.teacher_full_name is None


async def test_open_gym_with_teacher_and_existing_teacher_backed_behavior_remain_valid() -> None:
    marker = uuid.uuid4().hex
    start_date = datetime.now(UTC).date() + timedelta(days=1)

    async with AsyncSessionLocal() as db:
        admin = _admin_user(marker)
        teacher = _teacher(marker)
        open_gym = _gym_class(marker, ActivityType.open_gym)
        group_class = _gym_class(marker, ActivityType.group_class)
        db.add_all([admin, teacher, open_gym, group_class])
        await db.commit()
        teacher_id = teacher.id

        open_result = await create_class_schedule(
            db=db,
            schedule_in=_schedule_create(
                open_gym.id,
                teacher_id=teacher_id,
                start_date=start_date,
                start_hour=11,
            ),
            current_user=admin,  # type: ignore[arg-type]
        )
        group_result = await create_class_schedule(
            db=db,
            schedule_in=_schedule_create(
                group_class.id,
                teacher_id=teacher_id,
                start_date=start_date,
                start_hour=13,
            ),
            current_user=admin,  # type: ignore[arg-type]
        )

    assert open_result.teacher_id == teacher_id
    assert open_result.teacher is not None
    assert group_result.teacher_id == teacher_id
    assert group_result.teacher is not None


async def test_teacherless_non_open_gym_create_is_rejected() -> None:
    marker = uuid.uuid4().hex
    start_date = datetime.now(UTC).date() + timedelta(days=1)

    async with AsyncSessionLocal() as db:
        admin = _admin_user(marker)
        group_class = _gym_class(marker, ActivityType.group_class)
        db.add_all([admin, group_class])
        await db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await create_class_schedule(
                db=db,
                schedule_in=_schedule_create(
                    group_class.id,
                    teacher_id=None,
                    start_date=start_date,
                ),
                current_user=admin,  # type: ignore[arg-type]
            )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "requieren profesor" in str(exc_info.value.detail)


async def test_update_allows_teacherless_open_gym_and_rejects_teacherless_group_class() -> None:
    marker = uuid.uuid4().hex
    start_date = datetime.now(UTC).date() + timedelta(days=1)

    async with AsyncSessionLocal() as db:
        admin = _admin_user(marker)
        teacher = _teacher(marker)
        open_gym = _gym_class(marker, ActivityType.open_gym)
        group_class = _gym_class(marker, ActivityType.group_class)
        open_schedule = ClassSchedule(
            gym_class=open_gym,
            teacher=teacher,
            rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(15, 0),
            duration_minutes=60,
            capacity=8,
            start_date=start_date,
        )
        group_schedule = ClassSchedule(
            gym_class=group_class,
            teacher=teacher,
            rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(17, 0),
            duration_minutes=60,
            capacity=8,
            start_date=start_date,
        )
        db.add_all(
            [
                admin,
                teacher,
                open_gym,
                group_class,
                open_schedule,
                group_schedule,
            ]
        )
        await db.commit()
        teacher_id = teacher.id

        open_result = await update_class_schedule(
            db=db,
            schedule_id=open_schedule.id,
            schedule_in=ClassScheduleUpdate(teacher_id=None),
            current_user=admin,  # type: ignore[arg-type]
            regenerate=False,
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_class_schedule(
                db=db,
                schedule_id=group_schedule.id,
                schedule_in=ClassScheduleUpdate(teacher_id=None),
                current_user=admin,  # type: ignore[arg-type]
                regenerate=False,
            )

        stored_group = await class_schedule_crud.get(
            db=db,
            obj_id=group_schedule.id,
        )

    assert open_result.teacher_id is None
    assert open_result.teacher is None
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "requieren profesor" in str(exc_info.value.detail)
    assert stored_group is not None
    assert stored_group.teacher_id == teacher_id

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import ActivityType, BookingStatus, ClassSessionStatus, UserRole
from app.crud.crud_booking import booking as booking_crud
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


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Booking CRUD integration tests require fitflow_test; "
        f"configured database is {database_name!r}."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_get_does_not_require_soft_delete_contract() -> None:
    token = uuid.uuid4().hex

    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"crud-get-teacher-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="CRUD",
            last_name="Teacher",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"CRUD get class {token}",
            description="Booking CRUD get contract regression",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=4,
        )
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
            start_time=time(12, 0),
            duration_minutes=60,
            capacity=4,
            start_date=datetime.now(UTC).date(),
        )
        starts_at = datetime.now(UTC) + timedelta(days=2)
        class_session = ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=4,
            status=ClassSessionStatus.scheduled,
        )
        client_user = User(
            email=f"crud-get-client-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        )
        client = Client(
            first_name="CRUD",
            last_name="Client",
            document_number=f"crud-get-{token}",
            user=client_user,
        )

        db.add_all(
            [
                teacher,
                gym_class,
                schedule,
                class_session,
                client,
            ]
        )
        await db.flush()

        booking = Booking(
            client_id=client.id,
            class_session_id=class_session.id,
            status=BookingStatus.confirmed,
        )
        db.add(booking)
        await db.flush()

        booking_id = booking.id
        client_id = client.id
        session_id = class_session.id
        schedule_id = schedule.id
        gym_class_id = gym_class.id

        await db.commit()

    assert not hasattr(Booking, "deleted_at")

    async with AsyncSessionLocal() as db:
        loaded = await booking_crud.get(
            db=db,
            obj_id=booking_id,
            include_relations=True,
        )

        assert loaded is not None
        assert loaded.id == booking_id
        assert loaded.client.id == client_id
        assert loaded.class_session.id == session_id
        assert loaded.class_session.class_schedule.id == schedule_id
        assert loaded.class_session.class_schedule.gym_class.id == gym_class_id

        print(
            "FITFLOW_CRUD_GET_EVIDENCE "
            f"returned=true "
            f"identity_match={loaded.id == booking_id} "
            f"booking_has_deleted_at={hasattr(Booking, 'deleted_at')} "
            "relations_loaded=true"
        )
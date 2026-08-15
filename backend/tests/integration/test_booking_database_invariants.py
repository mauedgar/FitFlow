import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    UserRole,
)
from app.crud.crud_booking import booking as booking_crud
from app.crud.crud_class_session import class_session as class_session_crud
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
from app.schemas.booking import BookingCreateInternal
from app.services.errors import ConflictError
from app.services.front_desk_service import check_in_booking


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test():
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    """Fail before opening a connection unless the configured DB is fitflow_test."""
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Integration tests require the isolated fitflow_test database; "
        f"configured database is {database_name!r}."
    )


async def _client(db: AsyncSession, suffix: str) -> Client:
    user = User(
        email=f"orm-{suffix}-{uuid.uuid4()}@example.test",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    client = Client(
        first_name="Test",
        last_name="Client",
        document_number=str(uuid.uuid4()),
        user=user,
    )
    db.add(client)
    await db.flush()
    return client


async def _session_with_clients(client_count: int = 1) -> tuple[uuid.UUID, list[uuid.UUID]]:
    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"teacher-{uuid.uuid4()}@example.test",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="Test",
            last_name="Teacher",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"Test class {uuid.uuid4()}",
            description="Integration test class",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=1,
        )
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
            start_time=time(10, 0),
            duration_minutes=60,
            capacity=1,
            start_date=date.today(),
        )
        starts_at = datetime.now(UTC) + timedelta(days=1)
        session = ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=1,
            status=ClassSessionStatus.scheduled,
        )
        clients = [await _client(db, str(index)) for index in range(client_count)]
        db.add_all([teacher, gym_class, schedule, session])
        await db.commit()
        return session.id, [client.id for client in clients]


async def _count_bookings(session_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as db:
        return int(
            (
                await db.scalar(
                    select(ClassSession.current_bookings_count).where(
                        ClassSession.id == session_id
                    )
                )
            )
            or 0
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancelled_booking_releases_capacity_and_allows_rebooking() -> None:
    session_id, client_ids = await _session_with_clients()
    client_id = client_ids[0]

    async with AsyncSessionLocal() as db:
        first = Booking(
            client_id=client_id,
            class_session_id=session_id,
            status=BookingStatus.confirmed,
        )
        db.add(first)
        await db.commit()
        first.status = BookingStatus.cancelled
        first.cancelled_at = datetime.now(UTC)
        db.add(first)
        await db.commit()

        replacement = Booking(
            client_id=client_id,
            class_session_id=session_id,
            status=BookingStatus.confirmed,
        )
        db.add(replacement)
        await db.commit()

    assert await _count_bookings(session_id) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_deleting_session_preserves_booking_history() -> None:
    session_id, client_ids = await _session_with_clients()

    async with AsyncSessionLocal() as db:
        booking = Booking(
            client_id=client_ids[0],
            class_session_id=session_id,
            status=BookingStatus.confirmed,
        )
        db.add(booking)
        await db.commit()

        session = await class_session_crud.get(db=db, obj_id=session_id)
        assert session is not None
        await class_session_crud.remove(db=db, db_obj=session)

    async with AsyncSessionLocal() as db:
        stored_session = await db.scalar(
            select(ClassSession).where(ClassSession.id == session_id)
        )
        booking_count = await db.scalar(
            select(func.count(Booking.id)).where(Booking.class_session_id == session_id)
        )
        assert stored_session is not None
        assert stored_session.active is False
        assert stored_session.deleted_at is not None
        assert booking_count == 1
        assert await class_session_crud.get(db=db, obj_id=session_id) is None


@pytest.mark.integration
@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_last_capacity_is_protected_by_row_lock() -> None:
    session_id, client_ids = await _session_with_clients(client_count=2)

    async def reserve(client_id: uuid.UUID) -> str:
        async with AsyncSessionLocal() as db:
            payload = BookingCreateInternal(
                client_id=client_id,
                class_session_id=session_id,
                created_at=datetime.now(UTC),
                status=BookingStatus.confirmed,
            )
            try:
                await booking_crud.create_with_capacity_check(
                    db,
                    client_id=client_id,
                    session_id=session_id,
                    obj_in=payload,
                )
            except ConflictError:
                return "conflict"
            return "created"

    results = await asyncio.gather(*(reserve(client_id) for client_id in client_ids))
    assert sorted(results) == ["conflict", "created"]
    assert await _count_bookings(session_id) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_front_desk_check_in_records_attendance_without_deleting_booking() -> None:
    session_id, client_ids = await _session_with_clients()

    async with AsyncSessionLocal() as db:
        booking = Booking(
            client_id=client_ids[0],
            class_session_id=session_id,
            status=BookingStatus.confirmed,
        )
        db.add(booking)
        await db.commit()
        booking_id = booking.id

    async with AsyncSessionLocal() as db:
        view = await check_in_booking(db, session_id=session_id, booking_id=booking_id)
        assert view.id == booking_id
        assert view.status == BookingStatus.attended

    async with AsyncSessionLocal() as db:
        stored = await db.get(Booking, booking_id)
        assert stored is not None
        assert stored.status == BookingStatus.attended
        assert stored.checked_in_at is not None

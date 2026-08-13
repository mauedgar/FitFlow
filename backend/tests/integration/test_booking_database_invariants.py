import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    UserRole,
)
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
from app.schemas.booking import BookingCreateInternal
from app.services.errors import ConflictError


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test():
    yield
    await engine.dispose()


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
            days_of_week=[0],
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

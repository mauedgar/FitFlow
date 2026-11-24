import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

import httpx
import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    MembershipPlan,
    MembershipStatus,
    UserRole,
)
from auth_session_test_helpers import (
    committed_access, require_local_test_database,
    cleanup_synthetic_fixture, finish_synthetic_cleanup, require_postgres15_test_service,
)
from app.crud.crud_booking import booking as booking_crud
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Teacher,
    User,
)
from app.db.session import AsyncSessionLocal, engine
from app.main import app
from app.schemas.booking import BookingCreateInternal


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    require_local_test_database()


@pytest.fixture
async def booking_fixture() -> AsyncIterator[tuple[UUID, str]]:
    await require_postgres15_test_service()
    token = uuid.uuid4().hex
    teacher_user_id = uuid.uuid4()
    client_user_id = uuid.uuid4()
    gym_class_id = uuid.uuid4()
    schedule_id = uuid.uuid4()
    class_session_id = uuid.uuid4()
    client_email = f"booking-boundary-client-{token}@example.com"

    try:
        async with AsyncSessionLocal() as db:
            teacher_user = User(
                id=teacher_user_id,
                email=f"booking-boundary-teacher-{token}@example.com",
                hashed_password="not-a-real-password",
                role=UserRole.teacher,
            )
            teacher = Teacher(
                first_name="Boundary",
                last_name="Teacher",
                user=teacher_user,
            )
            gym_class = GymClass(
                id=gym_class_id,
                name=f"Boundary class {token}",
                description="Booking HTTP transaction boundary regression",
                activity_type=ActivityType.group_class,
                duration_minutes=60,
                default_capacity=2,
            )
            schedule = ClassSchedule(
                id=schedule_id,
                gym_class=gym_class,
                teacher=teacher,
                rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
                start_time=time(10, 0),
                duration_minutes=60,
                capacity=2,
                start_date=datetime.now(UTC).date(),
            )
            starts_at = datetime.now(UTC) + timedelta(days=2)
            class_session = ClassSession(
                id=class_session_id,
                class_schedule=schedule,
                starts_at=starts_at,
                ends_at=starts_at + timedelta(hours=1),
                capacity_snapshot=2,
                status=ClassSessionStatus.scheduled,
            )
            client_user = User(
                id=client_user_id,
                email=client_email,
                hashed_password="not-a-real-password",
                role=UserRole.client,
            )
            client = Client(
                first_name="Boundary",
                last_name="Client",
                document_number=token,
                user=client_user,
            )
            membership = Membership(
                client=client,
                plan=MembershipPlan.gym_only,
                status=MembershipStatus.active,
                end_date=datetime.now(UTC) + timedelta(days=30),
            )

            db.add_all(
                [
                    teacher,
                    gym_class,
                    schedule,
                    class_session,
                    client,
                    membership,
                ]
            )
            await db.flush()
            session_id = class_session.id
            await db.commit()
        access_token = await committed_access(client_user_id, UserRole.client.value)
        yield session_id, access_token
    finally:
        await finish_synthetic_cleanup(cleanup_synthetic_fixture(
            user_ids=(teacher_user_id, client_user_id),
            class_session_ids=(class_session_id,),
            class_schedule_ids=(schedule_id,),
            gym_class_ids=(gym_class_id,),
        ))


async def _post_booking(
    *,
    session_id: UUID,
    access_token: str,
) -> httpx.Response:
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://fitflow.test",
    ) as client:
        return await client.post(
            f"{settings.API_V1_STR}/bookings/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "status": BookingStatus.confirmed.value,
                "class_session_id": str(session_id),
            },
        )


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_creation_hands_off_real_auth_transaction(
    monkeypatch: pytest.MonkeyPatch, booking_fixture: tuple[UUID, str],
) -> None:
    session_id, access_token = booking_fixture
    transaction_states_at_crud_entry: list[bool] = []
    original_create = booking_crud.create_with_capacity_check

    async def tracked_create_with_capacity_check(
        db: AsyncSession,
        *,
        client_id: UUID,
        session_id: UUID,
        obj_in: BookingCreateInternal,
    ) -> Booking:
        transaction_states_at_crud_entry.append(db.in_transaction())
        return await original_create(
            db,
            client_id=client_id,
            session_id=session_id,
            obj_in=obj_in,
        )

    monkeypatch.setattr(
        booking_crud,
        "create_with_capacity_check",
        tracked_create_with_capacity_check,
    )

    response = await _post_booking(
        session_id=session_id,
        access_token=access_token,
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert transaction_states_at_crud_entry == [False]


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_creation_allows_reference_capacity_overflow(
    booking_fixture: tuple[UUID, str],
) -> None:
    session_id, access_token = booking_fixture

    extra_user_id = uuid.uuid4()
    try:
        async with AsyncSessionLocal() as db:
            class_session = await db.get(ClassSession, session_id)
            assert class_session is not None
            class_session.capacity_snapshot = 1

            token = uuid.uuid4().hex
            existing_user = User(
                id=extra_user_id,
                email=f"booking-capacity-existing-{token}@example.com",
                hashed_password="not-a-real-password",
                role=UserRole.client,
            )
            existing_client = Client(
                first_name="Existing",
                last_name="Booking",
                document_number=f"existing-{token}",
                user=existing_user,
            )
            db.add(existing_client)
            await db.flush()
            db.add(
                Booking(
                    client_id=existing_client.id,
                    class_session_id=session_id,
                    status=BookingStatus.confirmed,
                )
            )
            await db.commit()

        response = await _post_booking(
            session_id=session_id,
            access_token=access_token,
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text

        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://fitflow.test",
        ) as client:
            capacity_response = await client.get(
                f"{settings.API_V1_STR}/bookings/sessions/{session_id}/can-book"
            )

        assert capacity_response.status_code == status.HTTP_200_OK, capacity_response.text
        assert capacity_response.json()["capacity"] == 1
        assert capacity_response.json()["used"] == 2
        assert capacity_response.json()["available"] == 0
        # A session is not authority to delete bookings/accounts of other users.
        with pytest.raises(RuntimeError, match="retained booking"):
            await cleanup_synthetic_fixture(user_ids=(), class_session_ids=(session_id,))
        async with AsyncSessionLocal() as db:
            assert await db.get(User, extra_user_id) is not None
            assert await db.scalar(select(Booking.id).where(
                Booking.class_session_id == session_id, Booking.client_id == existing_client.id
            )) is not None
    finally:
        # This user was explicitly minted by THIS test, not inferred from Booking.
        await finish_synthetic_cleanup(cleanup_synthetic_fixture(
            user_ids=(extra_user_id,),
        ))


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_booking_still_maps_to_http_409(
    booking_fixture: tuple[UUID, str],
) -> None:
    session_id, access_token = booking_fixture

    first = await _post_booking(
        session_id=session_id,
        access_token=access_token,
    )
    duplicate = await _post_booking(
        session_id=session_id,
        access_token=access_token,
    )

    assert first.status_code == status.HTTP_201_CREATED, first.text
    assert duplicate.status_code == status.HTTP_409_CONFLICT, duplicate.text
    assert duplicate.json()["detail"] == "Ya tienes una reserva para esta sesi\u00f3n."

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    UserRole,
)
from app.core.security import create_access_token
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
from app.main import app


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Booking cancellation API tests require fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _fixture(
    *,
    caller_role: UserRole | None,
    caller_owns_booking: bool = False,
) -> tuple[UUID, str | None]:
    token = uuid.uuid4().hex
    owner_email = f"cancel-owner-{token}@example.com"

    async with AsyncSessionLocal() as db:
        teacher_user = User(
            email=f"cancel-instructor-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.teacher,
        )
        teacher = Teacher(
            first_name="Cancel",
            last_name="Instructor",
            user=teacher_user,
        )
        gym_class = GymClass(
            name=f"Cancellation class {token}",
            description="Booking cancellation authorization regression",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=8,
        )
        schedule = ClassSchedule(
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=WEEKLY;BYDAY=MO",
            start_time=time(11, 0),
            duration_minutes=60,
            capacity=8,
            start_date=datetime.now(UTC).date(),
        )
        starts_at = datetime.now(UTC) + timedelta(days=3)
        class_session = ClassSession(
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=8,
            status=ClassSessionStatus.scheduled,
        )

        owner_user = User(
            email=owner_email,
            hashed_password="not-a-real-password",
            role=UserRole.client,
        )
        owner = Client(
            first_name="Cancellation",
            last_name="Owner",
            document_number=f"owner-{token}",
            user=owner_user,
        )

        db.add_all([teacher, gym_class, schedule, class_session, owner])

        caller_email: str | None = None

        if caller_role == UserRole.client and caller_owns_booking:
            caller_email = owner_email
        elif caller_role is not None:
            caller_email = f"cancel-caller-{caller_role.value}-{token}@example.com"
            caller_user = User(
                email=caller_email,
                hashed_password="not-a-real-password",
                role=caller_role,
            )
            db.add(caller_user)

            if caller_role == UserRole.client:
                caller_client = Client(
                    first_name="Cancellation",
                    last_name="NonOwner",
                    document_number=f"caller-{token}",
                    user=caller_user,
                )
                db.add(caller_client)

        await db.flush()

        booking = Booking(
            client_id=owner.id,
            class_session_id=class_session.id,
            status=BookingStatus.confirmed,
        )
        db.add(booking)
        await db.flush()

        booking_id = booking.id
        await db.commit()

    if caller_email is None:
        return booking_id, None

    access_token = create_access_token(
        {
            "sub": caller_email,
            "role": caller_role.value if caller_role is not None else "",
        }
    )
    return booking_id, access_token


async def _post_cancel(
    *,
    booking_id: UUID,
    access_token: str | None,
) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    headers: dict[str, str] = {}
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://fitflow.test",
    ) as client:
        return await client.post(
            f"{settings.API_V1_STR}/bookings/{booking_id}/cancel",
            headers=headers,
        )


async def _stored_status(booking_id: UUID) -> BookingStatus:
    async with AsyncSessionLocal() as db:
        booking = await db.get(Booking, booking_id)
        assert booking is not None
        return booking.status


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_cancel_client_owner() -> None:
    booking_id, token = await _fixture(
        caller_role=UserRole.client,
        caller_owns_booking=True,
    )
    response = await _post_cancel(booking_id=booking_id, access_token=token)
    stored = await _stored_status(booking_id)

    print(
        "FITFLOW_AUTH_EVIDENCE "
        f"case=client_owner http={response.status_code} booking={stored.value}"
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert stored == BookingStatus.cancelled


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_cancel_client_non_owner() -> None:
    booking_id, token = await _fixture(
        caller_role=UserRole.client,
        caller_owns_booking=False,
    )
    response = await _post_cancel(booking_id=booking_id, access_token=token)
    stored = await _stored_status(booking_id)

    print(
        "FITFLOW_AUTH_EVIDENCE "
        f"case=client_non_owner http={response.status_code} booking={stored.value}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert stored == BookingStatus.confirmed


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_cancel_admin_without_client_profile() -> None:
    booking_id, token = await _fixture(caller_role=UserRole.admin)
    response = await _post_cancel(booking_id=booking_id, access_token=token)
    stored = await _stored_status(booking_id)

    print(
        "FITFLOW_AUTH_EVIDENCE "
        f"case=admin_without_client_profile http={response.status_code} "
        f"booking={stored.value} admin_client_profile=false"
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert stored == BookingStatus.cancelled


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_cancel_unauthenticated() -> None:
    booking_id, token = await _fixture(caller_role=None)
    assert token is None

    response = await _post_cancel(booking_id=booking_id, access_token=None)
    stored = await _stored_status(booking_id)

    print(
        "FITFLOW_AUTH_EVIDENCE "
        f"case=unauthenticated http={response.status_code} booking={stored.value}"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert stored == BookingStatus.confirmed


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_booking_cancel_authenticated_disallowed_teacher() -> None:
    booking_id, token = await _fixture(caller_role=UserRole.teacher)
    response = await _post_cancel(booking_id=booking_id, access_token=token)
    stored = await _stored_status(booking_id)

    print(
        "FITFLOW_AUTH_EVIDENCE "
        f"case=disallowed_teacher http={response.status_code} booking={stored.value}"
    )

    assert response.status_code >= status.HTTP_400_BAD_REQUEST, response.text
    assert stored == BookingStatus.confirmed

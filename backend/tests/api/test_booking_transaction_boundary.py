import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url
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
from app.core.security import create_access_token
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
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Booking API integration tests require fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _booking_fixture() -> tuple[UUID, str]:
    token = uuid.uuid4().hex
    client_email = f"booking-boundary-client-{token}@example.com"

    async with AsyncSessionLocal() as db:
        teacher_user = User(
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
            name=f"Boundary class {token}",
            description="Booking HTTP transaction boundary regression",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            default_capacity=2,
        )
        schedule = ClassSchedule(
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
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            capacity_snapshot=2,
            status=ClassSessionStatus.scheduled,
        )
        client_user = User(
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

    access_token = create_access_token(
        {
            "sub": client_email,
            "role": UserRole.client.value,
        }
    )
    return session_id, access_token


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id, access_token = await _booking_fixture()
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
async def test_duplicate_booking_still_maps_to_http_409() -> None:
    session_id, access_token = await _booking_fixture()

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

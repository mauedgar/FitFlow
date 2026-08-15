"""Structural contract tests for Pydantic v2 schemas."""

from datetime import date, datetime, time, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.enums import (
    ActivityType,
    AllowedPlan,
    BookingStatus,
    ClassSessionStatus,
    DifficultyLevel,
)
from app.schemas.booking import BookingCreate
from app.schemas.class_schedule import ClassScheduleCreate, ClassScheduleUpdate
from app.schemas.front_desk import FrontDeskBookingView, FrontDeskClassView
from app.schemas.membership import MembershipPublic
from app.schemas.user import UserPublic


def test_booking_create_requires_exactly_one_schedule_or_session_id() -> None:
    session_id = uuid4()
    schedule_id = uuid4()

    assert BookingCreate(
        status=BookingStatus.confirmed,
        class_session_id=session_id,
    ).class_session_id == session_id
    assert BookingCreate(
        status=BookingStatus.confirmed,
        class_schedule_id=schedule_id,
    ).class_schedule_id == schedule_id

    with pytest.raises(ValidationError):
        BookingCreate(status=BookingStatus.confirmed)
    with pytest.raises(ValidationError):
        BookingCreate(
            status=BookingStatus.confirmed,
            class_session_id=session_id,
            class_schedule_id=schedule_id,
        )


def test_schedule_contract_accepts_the_allowed_plan_restriction() -> None:
    schedule = ClassScheduleCreate(
        gym_class_id=uuid4(),
        teacher_id=uuid4(),
        rrule="RRULE:FREQ=WEEKLY;BYDAY=MO,WE",
        start_time=time(9, 0),
        duration_minutes=60,
        capacity=12,
        start_date=date(2026, 8, 13),
        allowed_plan=AllowedPlan.gym_only,
    )

    assert schedule.allowed_plan is AllowedPlan.gym_only
    assert ClassScheduleUpdate(allowed_plan=AllowedPlan.personalized).allowed_plan is AllowedPlan.personalized


def test_front_desk_views_serialize_core_enums() -> None:
    booking = FrontDeskBookingView(
        id=uuid4(),
        client_id=uuid4(),
        client_name="Cliente de prueba",
        client_email="cliente@example.test",
        status=BookingStatus.confirmed,
    )
    gym_class = FrontDeskClassView(
        id=uuid4(),
        name="Funcional",
        difficulty=DifficultyLevel.intermediate,
        activity_type=ActivityType.group_class,
    )

    assert booking.model_dump(mode="json")["status"] == BookingStatus.confirmed.value
    assert gym_class.model_dump(mode="json") == {
        "id": str(gym_class.id),
        "name": "Funcional",
        "difficulty": DifficultyLevel.intermediate.value,
        "activity_type": ActivityType.group_class.value,
    }
    assert ClassSessionStatus.open.value == "open"


def test_public_contracts_exclude_internal_fields() -> None:
    assert "password" not in UserPublic.model_fields
    assert {"created_at", "updated_at"}.isdisjoint(UserPublic.model_fields)
    assert "client_id" not in MembershipPublic.model_fields

    membership = MembershipPublic.model_validate(
        {
            "id": uuid4(),
            "plan": "premium",
            "status": "active",
            "start_date": datetime(2026, 8, 1, tzinfo=timezone.utc),
            "end_date": datetime(2026, 9, 1, tzinfo=timezone.utc),
            "is_active": True,
            "is_expired": False,
        }
    )
    assert membership.model_dump(mode="json")["plan"] == "premium"

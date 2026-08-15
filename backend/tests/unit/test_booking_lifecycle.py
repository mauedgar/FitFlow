from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest

from app.core.enums import BookingStatus, ClassSessionStatus, MembershipStatus
from app.db.models import Booking, ClassSession, Membership
from app.services.booking_service import (
    validate_booking_cancellation,
    validate_booking_creation,
)
from app.services.errors import BusinessValidationError, ConflictError


def _session(status: ClassSessionStatus) -> ClassSession:
    return cast(ClassSession, SimpleNamespace(
        status=status,
        starts_at=datetime.now(UTC) + timedelta(days=1),
        available_spots=1,
    ))


@pytest.mark.parametrize("status", [ClassSessionStatus.scheduled, ClassSessionStatus.open])
def test_future_scheduled_or_open_session_can_be_booked(status: ClassSessionStatus) -> None:
    membership = cast(Membership, SimpleNamespace(status=MembershipStatus.active))
    validate_booking_creation(_session(status), membership)


@pytest.mark.parametrize("status", [ClassSessionStatus.closed, ClassSessionStatus.cancelled, ClassSessionStatus.completed])
def test_non_reservable_session_states_are_rejected(status: ClassSessionStatus) -> None:
    membership = cast(Membership, SimpleNamespace(status=MembershipStatus.active))
    with pytest.raises(BusinessValidationError):
        validate_booking_creation(_session(status), membership)


def test_cancellation_rejects_a_second_cancellation() -> None:
    with pytest.raises(ConflictError):
        validate_booking_cancellation(cast(Booking, SimpleNamespace(status=BookingStatus.cancelled)))


@pytest.mark.parametrize("status", [BookingStatus.attended, BookingStatus.no_show])
def test_cancellation_does_not_rewrite_attendance_history(status: BookingStatus) -> None:
    with pytest.raises(BusinessValidationError):
        validate_booking_cancellation(cast(Booking, SimpleNamespace(status=status)))

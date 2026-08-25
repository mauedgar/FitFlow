"""Unit tests for schedule metrics over int capacity_snapshot."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from app.services.class_schedule_service import (
    get_schedule_next_session,
    get_schedule_occupancy,
)

if TYPE_CHECKING:
    from app.db.models.class_schedule import ClassSchedule


def _session(**overrides: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "id": uuid4(),
        "starts_at": datetime.now(UTC) + timedelta(hours=2),
        "capacity_snapshot": 7,
        "current_bookings_count": 3,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _schedule(*sessions: SimpleNamespace) -> "ClassSchedule":
    return cast("ClassSchedule", SimpleNamespace(class_sessions=list(sessions)))


def test_occupancy_uses_int_snapshot() -> None:
    assert get_schedule_occupancy(_schedule(_session())) == 3 / 7


def test_occupancy_without_sessions_or_capacity_is_zero() -> None:
    assert get_schedule_occupancy(_schedule()) == 0.0
    legacy = _session(capacity_snapshot=None)
    assert get_schedule_occupancy(_schedule(legacy)) == 0.0


def test_next_session_computes_available_spots_from_int_snapshot() -> None:
    info = get_schedule_next_session(_schedule(_session()))
    assert info is not None
    assert info.available_spots == 4
    assert info.current_bookings_count == 3


def test_next_session_returns_none_without_future_sessions() -> None:
    past = _session(starts_at=datetime.now(UTC) - timedelta(hours=1))
    assert get_schedule_next_session(_schedule(past)) is None

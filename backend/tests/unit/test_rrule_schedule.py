"""RRULE-only recurrence contract tests."""

from datetime import date, time
from typing import TypedDict
from uuid import UUID, uuid4

import pytest
from app.schemas.class_schedule import ClassScheduleCreate
from pydantic import ValidationError


class _SchedulePayload(TypedDict):
    gym_class_id: UUID
    teacher_id: UUID
    rrule: str
    start_time: time
    duration_minutes: int
    capacity: int
    start_date: date


def _payload(rrule: str) -> _SchedulePayload:
    return {
        "gym_class_id": uuid4(),
        "teacher_id": uuid4(),
        "rrule": rrule,
        "start_time": time(9, 0),
        "duration_minutes": 60,
        "capacity": 12,
        "start_date": date(2026, 8, 13),
    }


def test_rrule_is_normalized_and_parseable() -> None:
    schedule = ClassScheduleCreate(**_payload("rrule:freq=weekly;byday=mo,we"))
    assert schedule.rrule == "RRULE:FREQ=WEEKLY;BYDAY=MO,WE"


@pytest.mark.parametrize("rrule", ["FREQ=WEEKLY", "DTSTART:20260813T090000\nRRULE:FREQ=WEEKLY", "RRULE:INVALID"])
def test_rrule_rejects_invalid_or_noncanonical_values(rrule: str) -> None:
    with pytest.raises(ValidationError):
        ClassScheduleCreate(**_payload(rrule))

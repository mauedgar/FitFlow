"""RRULE-only recurrence contract tests."""

from datetime import date, time
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.class_schedule import ClassScheduleCreate


def _payload(rrule: str) -> dict[str, object]:
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

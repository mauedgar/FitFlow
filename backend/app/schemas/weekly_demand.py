"""Schemas for the weekly expected-demand read contract."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ActivityType, ClassSessionStatus


class WeeklyScheduleDemandItem(BaseModel):
    """Expected Booking demand for one concrete scheduled occurrence."""

    session_id: UUID
    class_schedule_id: UUID
    activity_id: UUID
    activity_name: str
    activity_type: ActivityType
    starts_at: datetime
    ends_at: datetime
    status: ClassSessionStatus
    active_booking_count: int
    reference_capacity: int | None = None
    booking_occupancy_ratio: float | None = None

    model_config = ConfigDict(from_attributes=True)


class WeeklyScheduleDemandView(BaseModel):
    """Seven-day local-calendar demand projection."""

    week_start: date
    week_end_exclusive: date
    items: list[WeeklyScheduleDemandItem] = Field(default_factory=list)

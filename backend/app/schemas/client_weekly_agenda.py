"""Schemas for the authenticated Client weekly agenda read contract."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import BookingStatus
from app.schemas.weekly_demand import WeeklyScheduleDemandItem


class ClientWeeklyAgendaBookingState(BaseModel):
    """Current non-cancelled Booking owned by the authenticated Client."""

    booking_id: UUID
    status: BookingStatus


class ClientWeeklyAgendaItem(WeeklyScheduleDemandItem):
    """One eligible concrete occurrence in the Client's weekly agenda."""

    membership_plan_eligible: bool
    own_booking: ClientWeeklyAgendaBookingState | None = None


class ClientWeeklyAgendaView(BaseModel):
    """Seven-day local-calendar agenda for the authenticated Client."""

    week_start: date
    week_end_exclusive: date
    items: list[ClientWeeklyAgendaItem] = Field(default_factory=list)

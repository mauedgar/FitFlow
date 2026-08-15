"""Schemas operativos para el módulo Front Desk.

Estas vistas simplifican la información para mesa de entrada,
sin exponer relaciones profundas ni datos sensibles.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    ActivityType,
    BookingStatus,
    ClassSessionStatus,
    DifficultyLevel,
)

# --------------------------------------------------------------------------- #
# CAPACIDAD DE SESIÓN
# --------------------------------------------------------------------------- #

class SessionCapacity(BaseModel):
    """Representa la capacidad disponible de una sesión."""

    session_id: UUID
    capacity: int
    used: int
    available: int

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# SESIÓN DEL DÍA (vista operativa)
# --------------------------------------------------------------------------- #

class FrontDeskSessionView(BaseModel):
    """Vista simplificada de una sesión para front desk."""

    id: UUID
    class_schedule_id: UUID
    gym_class_id: UUID
    teacher_id: UUID

    starts_at: datetime
    ends_at: datetime
    status: ClassSessionStatus

    gym_class_name: str
    teacher_full_name: str

    capacity_snapshot: int
    current_bookings_count: int
    available_spots: int

    is_live: bool
    is_upcoming: bool
    is_full: bool
    is_empty: bool

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# SESIÓN DETALLADA (vista operativa)
# --------------------------------------------------------------------------- #

class FrontDeskSessionDetailView(FrontDeskSessionView):
    """Vista detallada de una sesión, con reservas incluidas."""

    bookings: list[FrontDeskBookingView]


# --------------------------------------------------------------------------- #
# RESERVA EN SESIÓN (vista operativa)
# --------------------------------------------------------------------------- #

class FrontDeskBookingView(BaseModel):
    """Vista simplificada de una reserva dentro de una sesión."""

    id: UUID
    client_id: UUID
    client_name: str
    client_email: str
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# CLASE ACTIVA (vista operativa)
# --------------------------------------------------------------------------- #

class FrontDeskClassView(BaseModel):
    """Vista simplificada de una clase activa."""

    id: UUID
    name: str
    difficulty: DifficultyLevel | None
    activity_type: ActivityType

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# VISTA DEL DÍA COMPLETO
# --------------------------------------------------------------------------- #

class FrontDeskDayView(BaseModel):
    """Vista operativa del día completo."""

    date: date
    sessions: list[FrontDeskSessionView]

    model_config = ConfigDict(from_attributes=True)

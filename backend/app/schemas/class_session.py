"""
Schemas para ClassSession (Sprint 6–7)
--------------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (ClassSession)
• Esquema público (ClassSessionPublic)
• Extensiones con disponibilidad
• Esquemas compactos para anidamiento
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

# Evitar circularidad
if TYPE_CHECKING:
    from .booking import BookingPublic
    from .class_schedule import (
        ClassScheduleInClassSessionResponse,
        ClassSchedulePublic,
        NextSessionInfo,
    )

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class ClassSessionBase(BaseModel):
    """Campos comunes de una sesión individual."""
    starts_at: datetime
    ends_at: datetime
    status: bool = False

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class ClassSessionCreate(ClassSessionBase):
    """Esquema para crear una sesión individual."""
    class_schedule_id: uuid.UUID


# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class ClassSessionUpdate(BaseModel):
    """Esquema para actualizar parcialmente una sesión."""
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: bool | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquema privado (operativo interno)
# --------------------------------------------------------------------------- #

class ClassSession(ClassSessionBase):
    """
    Esquema completo de una sesión (privado).
    Incluye:
        • relación con ClassSchedule
        • relación con Bookings
        • campos calculados de disponibilidad
    """
    id: uuid.UUID
    class_schedule_id: uuid.UUID

    class_schedule: ClassSchedulePublic
    bookings: list[BookingPublic] = Field(default_factory=list)

    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema público (frontend)
# --------------------------------------------------------------------------- #

class ClassSessionPublic(ClassSessionBase):
    """
    Versión pública de una sesión.
    Usada en:
        • frontend cliente
        • catálogo público
        • listados públicos de sesiones
    """
    id: uuid.UUID
    class_schedule_id: uuid.UUID

    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Sesión con datos extendidos (público)
# --------------------------------------------------------------------------- #

class ClassSessionWithSchedule(ClassSessionPublic):
    """
    Extiende ClassSessionPublic con datos públicos del horario.
    Usado en:
        • detalle de sesión
        • front_desk
    """
    class_schedule: ClassSchedulePublic


# --------------------------------------------------------------------------- #
# 7. Sesión con próxima sesión (si se usa en dashboards)
# --------------------------------------------------------------------------- #

class ClassSessionWithNext(ClassSessionPublic):
    """
    Extiende ClassSessionPublic con información de la próxima sesión.
    Usado en:
        • dashboards
        • front_desk
    """
    next_session: NextSessionInfo | None = None


# --------------------------------------------------------------------------- #
# 8. Esquema compacto para anidamiento en ClassSchedule o GymClass
# --------------------------------------------------------------------------- #

class ClassSessionInResponse(ClassSessionBase):
    """
    Versión compacta de la sesión para anidarla dentro de ClassSchedule o GymClass.
    Incluye campos calculados pero no relaciones completas.
    """
    id: uuid.UUID
    class_schedule_id: uuid.UUID

    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 9. Esquema compacto dentro de Booking
# --------------------------------------------------------------------------- #

class ClassSessionInBookingResponse(ClassSessionBase):
    """
    Versión compacta de la sesión dentro de Booking.
    Incluye solo la relación mínima necesaria.
    """
    id: uuid.UUID
    class_schedule_id: uuid.UUID
    class_schedule: ClassScheduleInClassSessionResponse

    model_config = ConfigDict(from_attributes=True)

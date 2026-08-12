"""Schemas para ClassSession (Sprint 6-7).

--------------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (ClassSession)
• Esquema público (ClassSessionPublic)
• Extensiones con disponibilidad
• Esquemas compactos para anidamiento
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ClassSessionStatus  # noqa: TC001
from app.schemas.class_schedule import (
    ClassScheduleInClassSessionResponse,  # noqa: TC001
    ClassSchedulePublic,  # noqa: TC001
    NextSessionInfo,  # noqa: TC001
)

# Evitar circularidad: booking.py importa class_session.py
if TYPE_CHECKING:

    from app.schemas.booking import BookingPublic


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

    class_schedule_id: UUID


# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class ClassSessionUpdate(BaseModel):
    """Esquema para actualizar parcialmente una sesión."""

    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: ClassSessionStatus | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquema privado (operativo interno)
# --------------------------------------------------------------------------- #

class ClassSession(ClassSessionBase):
    """Esquema completo de una sesión (privado).

    Incluye:
        • relación con ClassSchedule
        • relación con Bookings
        • campos calculados de disponibilidad.
    """

    id: UUID
    class_schedule_id: UUID

    class_schedule: ClassSchedulePublic
    bookings: list["BookingPublic"] = Field(default_factory=list)  # noqa: UP037

    current_bookings_count: int = 0
    available_spots: int = 0
    capacity_snapshot: int

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema público (frontend)
# --------------------------------------------------------------------------- #

class ClassSessionPublic(ClassSessionBase):
    """Versión pública de una sesión.

    Usada en:
        • frontend cliente
        • catálogo público
        • listados públicos de sesiones.
    """

    id: UUID
    class_schedule_id: UUID

    current_bookings_count: int = 0
    available_spots: int = 0
    capacity_snapshot: int

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Sesión con datos extendidos (público)
# --------------------------------------------------------------------------- #

class ClassSessionWithSchedule(ClassSessionPublic):
    """Extiende ClassSessionPublic con datos públicos del horario.

    • detalle de sesión
        • front_desk.
    """

    capacity_snapshot: int
    class_schedule: ClassSchedulePublic


# --------------------------------------------------------------------------- #
# 7. Sesión con próxima sesión (si se usa en dashboards)
# --------------------------------------------------------------------------- #

class ClassSessionWithNext(ClassSessionPublic):
    """Extiende ClassSessionPublic con información de la próxima sesión.

    Usado en:
        • dashboards
        • front_desk.
    """

    next_session: NextSessionInfo | None = None


# --------------------------------------------------------------------------- #
# 8. Esquema compacto para anidamiento en ClassSchedule o GymClass
# --------------------------------------------------------------------------- #

class ClassSessionInResponse(ClassSessionBase):
    """Versión compacta de la sesión para anidarla dentro de ClassSchedule o GymClass.

    Incluye campos calculados pero no relaciones completas.
    """

    id: UUID
    class_schedule_id: UUID

    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 9. Esquema compacto dentro de Booking
# --------------------------------------------------------------------------- #

class ClassSessionInBookingResponse(ClassSessionBase):
    """Versión compacta de la sesión dentro de Booking.

    Incluye solo la relación mínima necesaria.
    """

    id: UUID
    class_schedule_id: UUID
    class_schedule: ClassScheduleInClassSessionResponse

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 10. Sesión completa con todas las relaciones (detalle)
# --------------------------------------------------------------------------- #

class ClassSessionWithRelations(ClassSessionBase):
    """Sesión completa con todas sus relaciones cargadas.

    Incluye:
        • class_schedule (público)
        • gym_class (público)
        • teacher (público)
        • bookings (público)
        • campos calculados
    Usado en:
        • /sessions/{id}
        • front desk
        • dashboards internos
    """

    id: UUID
    class_schedule_id: UUID

    class_schedule: ClassSchedulePublic
    gym_class: ClassSchedulePublic.gym_class.__class__  # type: ignore[attr-defined]
    teacher: ClassSchedulePublic.teacher.__class__  # type: ignore[attr-defined]

    bookings: list["BookingPublic"] = Field(default_factory=list)  # noqa: UP037

    capacity_snapshot: int
    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 11. Resolver forward refs
# --------------------------------------------------------------------------- #

ClassSession.model_rebuild()
ClassSessionWithRelations.model_rebuild()

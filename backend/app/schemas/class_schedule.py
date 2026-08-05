"""Schemas para ClassSchedule (Sprint 6-7).

---------------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (ClassSchedule)
• Esquema público (ClassSchedulePublic)
• Extensiones con próxima sesión
• Esquemas compactos para anidamiento
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

# Evitar circularidad
if TYPE_CHECKING:
    import uuid
    from datetime import date, datetime, time

    from .class_session import ClassSessionInResponse, NextSessionInfo
    from .gym_class import GymClassInClassScheduleResponse, GymClassPublic
    from .teacher import (
        TeacherInClassScheduleResponse,
        TeacherInScheduleResponseMini,
    )


# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class ClassScheduleBase(BaseModel):
    """Campos comunes del horario recurrente."""

    days_of_week: list[int] = Field(..., min_length=1, max_length=7)
    start_time: time
    duration_minutes: int = Field(..., ge=1)
    capacity: int = Field(..., ge=1)
    start_date: date
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class ClassScheduleCreate(ClassScheduleBase):
    """Esquema para crear un horario recurrente."""

    gym_class_id: uuid.UUID
    teacher_id: uuid.UUID


# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class ClassScheduleUpdate(BaseModel):
    """Esquema para actualizar parcialmente un horario recurrente."""

    days_of_week: list[int] | None = None
    start_time: time | None = None
    duration_minutes: int | None = None
    capacity: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    gym_class_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquema privado (operativo)
# --------------------------------------------------------------------------- #

class ClassSchedule(ClassScheduleBase):
    """Esquema completo del horario recurrente (privado).

    Incluye:
        • gym_class
        • teacher
        • sesiones futuras.
    """

    id: uuid.UUID
    gym_class_id: uuid.UUID
    teacher_id: uuid.UUID

    gym_class: GymClassInClassScheduleResponse
    teacher: TeacherInClassScheduleResponse

    future_sessions: list[ClassSessionInResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema público
# --------------------------------------------------------------------------- #

class ClassSchedulePublic(BaseModel):
    """Versión pública del horario.

    Usada en:
        • TeacherPublic
        • GymClassWithSchedules
        • listados públicos.
    """

    id: uuid.UUID
    days_of_week: list[int]
    start_time: time
    duration_minutes: int
    capacity: int

    gym_class: GymClassPublic

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Esquema compacto dentro de ClassSession
# --------------------------------------------------------------------------- #

class ClassScheduleInClassSessionResponse(BaseModel):
    """Versión compacta del horario dentro de una sesión."""

    gym_class: GymClassPublic
    teacher: TeacherInScheduleResponseMini

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 7. Información calculada
# --------------------------------------------------------------------------- #

class NextSessionInfo(BaseModel):
    """Información calculada sobre la próxima sesión futura."""

    starts_at: datetime
    available_spots: int

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 8. Extensión con próxima sesión
# --------------------------------------------------------------------------- #

class ClassScheduleWithNextSession(ClassSchedulePublic):
    """Extiende ClassSchedulePublic con la próxima sesión futura.

    Usado en:
        • frontend cliente
        • dashboards
        • front_desk
    """

    next_session: NextSessionInfo | None = None

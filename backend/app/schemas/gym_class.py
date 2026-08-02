# app/schemas/gym_class.py
"""
Pydantic Schemas para el recurso GymClass
=========================================
Se definen los cuatro esquemas clásicos:

• GymClassBase   – Campos comunes y obligatorios.
• GymClassCreate – Para peticiones POST  (hereda todo de Base).
• GymClassUpdate – Para peticiones PATCH (todos los campos opcionales).
• GymClassRead   – Para respuestas, incluye id + timestamps + flags.

Además se incluyen dos esquemas simplificados para anidamiento:
• GymClassInClassScheduleResponse
• GymClassInTeacherResponse  (por si sigue siendo útil en el FE)

Author: FitFlow – Sprint 5
"""

from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from .base import IDSchema, TimestampSchema, SoftDeleteSchema
from .enums import ActivityType, DifficultyLevel


# --------------------------------------------------------------------------- #
#  BASE
# --------------------------------------------------------------------------- #
class GymClassBase(BaseModel):
    """
    Campos comunes a cualquier operación con GymClass.
    """
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(
        default=None,
        max_length=1_000,
        description="Descripción larga de la clase (markdown permitido)."
    )
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=240,
        description="Duración estándar de la clase en minutos."
    )
    difficulty: DifficultyLevel
    default_capacity: int = Field(
        ...,
        ge=1,
        description="Capacidad por defecto para las sesiones (puede sobreescribirse en el schedule)."
    )
    activity_type: ActivityType
    image_url: Optional[HttpUrl] = Field(
        default=None,
        description="URL pública de la imagen asociada a la clase."
    )

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
#  CREATE
# --------------------------------------------------------------------------- #
class GymClassCreate(GymClassBase):
    """
    Esquema para la creación de una nueva GymClass.
    No se permiten campos adicionales; hereda todo de GymClassBase.
    """
    pass


# --------------------------------------------------------------------------- #
#  UPDATE
# --------------------------------------------------------------------------- #
class GymClassUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una GymClass.
    Todos los campos son opcionales.
    """
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1_000)
    duration_minutes: Optional[int] = Field(None, ge=15, le=240)
    difficulty: Optional[DifficultyLevel] = None
    default_capacity: Optional[int] = Field(None, ge=1)
    activity_type: Optional[ActivityType] = None
    image_url: Optional[HttpUrl] = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
#  READ / RESPONSE
# --------------------------------------------------------------------------- #
class GymClassRead(IDSchema, GymClassBase, TimestampSchema, SoftDeleteSchema):
    """
    Esquema usado en las respuestas de la API para GymClass completo.
    Incluye:
      • id (UUID)
      • Campos de GymClassBase
      • Campos de tracking (created_at, updated_at)
      • Campos de soft-delete (deleted_at, active)
      • Schedules asociados (opcional, lazy load)
    """
    # Relación 1-N con ClassSchedule (lazy). Se puede completar vía `joinedload`
    class_schedules: list["ClassScheduleInResponse"] | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
#  ESQUEMAS REDUCIDOS PARA RESPUESTAS ANIDADAS
# --------------------------------------------------------------------------- #
class GymClassInClassScheduleResponse(GymClassBase, IDSchema):
    """
    Versión compacta para anidar dentro de ClassSchedule.
    No incluye timestamps ni flags.
    """
    model_config = ConfigDict(from_attributes=True)


class GymClassInTeacherResponse(GymClassBase, IDSchema):
    """
    Versión utilizada al listar las clases que un Teacher imparte
    (obtenidas a través de los ClassSchedule).
    """
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
#  IMPORTS DIFERIDOS PARA EVITAR CIRCULARIDAD
# --------------------------------------------------------------------------- #
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .class_schedule import ClassScheduleInResponse  # noqa: E402
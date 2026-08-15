"""Schemas para GymClass (Sprint 6-7).

----------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (GymClassRead)
• Esquema público (GymClassPublic)
• Extensiones con horarios y próxima sesión
• Esquemas compactos para anidamiento
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Evitar circularidad
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.core.enums import ActivityType, DifficultyLevel  # noqa: TC001
from app.schemas.base import IDSchema, SoftDeleteSchema, TimestampSchema
from app.schemas.class_schedule import ClassSchedulePublic

if TYPE_CHECKING:
    from app.schemas.class_schedule_refs import ClassScheduleInResponse

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class GymClassBase(BaseModel):
    """Campos comunes de una clase del gimnasio."""

    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)
    duration_minutes: int = Field(..., ge=15, le=240)
    difficulty: DifficultyLevel | None = None
    default_capacity: int = Field(..., ge=1)
    activity_type: ActivityType
    image_url: HttpUrl | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class GymClassCreate(GymClassBase):
    """Esquema para crear una nueva clase del gimnasio."""




# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class GymClassUpdate(BaseModel):
    """Esquema para actualizar parcialmente una clase del gimnasio."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    duration_minutes: int | None = Field(None, ge=15, le=240)
    difficulty: DifficultyLevel | None = None
    default_capacity: int | None = Field(None, ge=1)
    activity_type: ActivityType | None = None
    image_url: HttpUrl | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Respuesta completa (privada/operativa)
# --------------------------------------------------------------------------- #

class GymClassWithRelations(IDSchema, GymClassBase, TimestampSchema, SoftDeleteSchema):
    """Esquema completo para respuestas internas.

    Incluye:
    - id
    - campos base
    - timestamps
    - soft-delete
    - horarios asociados (lazy).
    """

    class_schedules: list[ClassScheduleInResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Versión pública
# --------------------------------------------------------------------------- #

class GymClassPublic(IDSchema, GymClassBase):
    """Versión pública de GymClass.

    No incluye timestamps, soft-delete ni schedules.
    """

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Extensiones públicas
# --------------------------------------------------------------------------- #

class GymClassWithSchedules(GymClassPublic):
    """Extiende GymClassPublic con horarios públicos.

    Usado en:
        • detalle de clase
        • catálogo enriquecido
        • frontend cliente.
    """

    schedules: list[ClassSchedulePublic] = Field(default_factory=list)

# --------------------------------------------------------------------------- #
# 7. Esquemas compactos para anidamiento
# --------------------------------------------------------------------------- #

class GymClassInClassScheduleResponse(GymClassBase, IDSchema):
    """Versión compacta para anidar dentro de ClassSchedule."""

    model_config = ConfigDict(from_attributes=True)


class GymClassInTeacherResponse(GymClassBase, IDSchema):
    """Versión compacta para anidar dentro de TeacherPublic."""

    model_config = ConfigDict(from_attributes=True)

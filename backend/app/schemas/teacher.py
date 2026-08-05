"""Schemas para Teacher (Sprint 6-7).

Incluye:
• Esquemas base heredados de Person
• Esquema privado (Teacher)
• Esquema público (TeacherPublic)
• Esquemas compactos para anidamiento
• Esquema mini para vistas operativas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from .person import PersonBase, PersonCreate, PersonUpdate

# Evitar circularidad
if TYPE_CHECKING:
    import uuid

    from .class_schedule import ClassSchedulePublic


# --------------------------------------------------------------------------- #
# 1. Base (hereda de Person)
# --------------------------------------------------------------------------- #

class TeacherBase(PersonBase):
    """Campos comunes del profesor."""

    bio: str | None = None
    cuil: str | None = None


class TeacherCreate(PersonCreate):
    """Esquema para crear un profesor."""

    bio: str | None = None
    cuil: str | None = None


class TeacherUpdate(PersonUpdate):
    """Esquema para actualizar un profesor."""

    bio: str | None = None
    cuil: str | None = None


# --------------------------------------------------------------------------- #
# 2. Esquema privado (solo admin/self)
# --------------------------------------------------------------------------- #

class Teacher(TeacherBase):
    """Perfil completo del profesor.

    Incluye:
        • datos sensibles (cuil)
        • horarios completos.
    """

    id: uuid.UUID
    class_schedules: list[ClassSchedulePublic] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 3. Esquema público / operativo
# --------------------------------------------------------------------------- #

class TeacherPublic(BaseModel):
    """Versión pública del profesor.

    NO incluye datos sensibles.
    Usada en:
        • listados públicos
        • vistas operativas
        • frontend
    """

    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    bio: str | None = None
    profile_image_url: str | None = None

    # Opcional: horarios públicos
    schedules: list[ClassSchedulePublic] | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquemas compactos (evitan circularidad)
# --------------------------------------------------------------------------- #

class TeacherInClassResponse(BaseModel):
    """Profesor dentro de una GymClass.

    Versión compacta y pública.
    NO incluye datos sensibles.
    """

    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    bio: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TeacherInClassScheduleResponse(BaseModel):
    """Profesor dentro de un ClassSchedule.

    Versión compacta para evitar cargar relaciones completas.
    """

    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema mini (ultra ligero)
# --------------------------------------------------------------------------- #

class TeacherInScheduleResponseMini(BaseModel):
    """Versión mínima del profesor.

    Usado en:
        • sesiones
        • front desk
        • dashboards
    """

    first_name: str
    last_name: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)

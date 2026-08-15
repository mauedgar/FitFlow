"""Schemas para Teacher (Sprint 6-7).

Incluye:
• Esquemas base heredados de Person
• Esquema privado (Teacher)
• Esquema público (TeacherPublic)
• Esquemas compactos para anidamiento
• Esquema mini para vistas operativas
"""

from __future__ import annotations  # noqa: I001

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.class_schedule import ClassSchedulePublic, NextSessionInfo  # noqa: TC001
from app.schemas.person import PersonBase, PersonCreate, PersonUpdate
from app.schemas.teacher_refs import (
    TeacherInClassScheduleResponse,
    TeacherInScheduleResponseMini,
)

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

class TeacherWithRelations(TeacherBase):
    """Perfil completo del profesor.

    Incluye:
        • datos sensibles (cuil)
        • horarios completos.
    """

    id: UUID
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

    id: UUID
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

    id: UUID
    first_name: str
    last_name: str
    full_name: str
    bio: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Esquema: Teacher con horarios públicos
# --------------------------------------------------------------------------- #

class TeacherWithSchedules(TeacherPublic):
    """Extiende el esquema público del profesor con sus horarios.

    Incluye:
        • Lista de horarios públicos (`ClassSchedulePublic`)
        • Ideal para vistas operativas y paneles administrativos.
    """

    schedules: list[ClassSchedulePublic] | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 7. Esquema: Teacher con próxima sesión futura
# --------------------------------------------------------------------------- #

class TeacherWithNextSession(TeacherPublic):
    """Extiende el esquema público del profesor con su próxima sesión futura.

    Incluye:
        • Información de la próxima sesión (`NextSessionInfo`)
        • Usado en dashboards, front desk y vistas de disponibilidad.
    """

    next_session: NextSessionInfo | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 8. Esquema: Teacher con métricas operativas
# --------------------------------------------------------------------------- #

class TeacherWithMetrics(TeacherPublic):
    """Extiende el esquema público del profesor con métricas operativas.

    Incluye:
        • total_classes → cantidad total de clases dictadas
        • future_sessions → cantidad de sesiones futuras
        • average_occupancy → ocupación promedio de las sesiones
    """

    total_classes: int = 0
    future_sessions: int = 0
    average_occupancy: float = 0.0

    model_config = ConfigDict(from_attributes=True)


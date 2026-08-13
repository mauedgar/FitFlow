"""Schemas compactos de Teacher sin dependencias circulares."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TeacherInClassScheduleResponse(BaseModel):
    """Profesor compacto dentro de un horario."""

    id: UUID
    first_name: str
    last_name: str
    full_name: str
    bio: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TeacherInScheduleResponseMini(BaseModel):
    """Profesor mínimo dentro de una sesión."""

    first_name: str
    last_name: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)

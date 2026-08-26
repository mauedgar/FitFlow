"""Schemas de GymClass reutilizables sin dependencias de otros dominios."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.core.enums import ActivityType, DifficultyLevel
from app.schemas.base import IDSchema


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


class GymClassPublic(IDSchema, GymClassBase):
    """Version publica de GymClass sin relaciones operativas."""

    model_config = ConfigDict(from_attributes=True)


class GymClassInClassScheduleResponse(GymClassBase, IDSchema):
    """Version compacta para anidar dentro de ClassSchedule."""

    model_config = ConfigDict(from_attributes=True)


class GymClassInTeacherResponse(GymClassBase, IDSchema):
    """Version compacta para anidar dentro de TeacherPublic."""

    model_config = ConfigDict(from_attributes=True)

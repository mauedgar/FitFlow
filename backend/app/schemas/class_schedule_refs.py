"""Schemas de ClassSchedule seguros para referencias entre modulos."""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import AllowedPlan
from app.schemas.gym_class_refs import GymClassPublic
from app.schemas.teacher_refs import TeacherInClassScheduleResponse


class ClassScheduleInResponse(BaseModel):
    """Horario compacto anidado dentro de otra respuesta."""

    id: UUID
    teacher: TeacherInClassScheduleResponse
    rrule: str
    start_time: time
    duration_minutes: int
    capacity: int
    allowed_plan: AllowedPlan
    active: bool

    model_config = ConfigDict(from_attributes=True)


class ClassSchedulePublic(BaseModel):
    """Version publica del horario reutilizable por schemas relacionados."""

    id: UUID
    rrule: str
    start_time: time
    duration_minutes: int
    capacity: int
    gym_class: GymClassPublic
    teacher: TeacherInClassScheduleResponse
    allowed_plan: AllowedPlan | None = None

    model_config = ConfigDict(from_attributes=True)


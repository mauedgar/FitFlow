"""Schemas compactos de ClassSession sin dependencias circulares."""

from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import AllowedPlan
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


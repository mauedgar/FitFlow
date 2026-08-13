"""Schemas compactos de ClassSession sin dependencias circulares."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import ClassSessionStatus


class ClassSessionInResponse(BaseModel):
    """Sesión compacta para respuestas anidadas."""

    id: UUID
    class_schedule_id: UUID
    starts_at: datetime
    ends_at: datetime
    status: ClassSessionStatus = ClassSessionStatus.scheduled
    current_bookings_count: int = 0
    available_spots: int = 0

    model_config = ConfigDict(from_attributes=True)

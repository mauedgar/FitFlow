"""Schemas compactos de Booking sin dependencias circulares."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import BookingStatus


class BookingPublic(BaseModel):
    """Versión pública y autocontenida de una reserva."""

    id: UUID
    status: BookingStatus
    starts_at: datetime
    ends_at: datetime
    gym_class_name: str

    model_config = ConfigDict(from_attributes=True)

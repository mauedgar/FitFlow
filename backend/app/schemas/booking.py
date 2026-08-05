"""Schemas para Booking (Sprint 6-7).

---------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (Booking)
• Esquema público (BookingPublic)
• Extensiones con cliente y sesión
• Esquemas compactos para anidamiento
• Esquema interno para capa de servicio
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, model_validator

# Evitar circularidad
if TYPE_CHECKING:
    import uuid
    from datetime import datetime

    from app.models.booking import BookingStatus

    from .class_session import ClassSessionInBookingResponse, ClassSessionPublic
    from .client import ClientInBookingResponse, ClientPublic

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class BookingBase(BaseModel):
    """Campos comunes de una reserva."""

    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class BookingCreate(BookingBase):
    """Esquema para crear una reserva.

    Regla de negocio:
        • class_session_id XOR class_schedule_id
    """

    class_session_id: uuid.UUID | None = None
    class_schedule_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_exactly_one_id_is_provided(self) -> BookingCreate:
        """Check un id."""
        has_session_id = self.class_session_id is not None
        has_schedule_id = self.class_schedule_id is not None

        if not (has_session_id ^ has_schedule_id):
            msg = "Debe proporcionar exclusivamente 'class_session_id' o 'class_schedule_id'."  # noqa: E501
            raise ValueError(
                msg,
            )
        return self


class BookingUpdate(BaseModel):
    """Esquema para actualizar parcialmente una reserva."""

    status: BookingStatus | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 3. Esquema privado (operativo)
# --------------------------------------------------------------------------- #

class Booking(BookingBase):
    """Esquema completo de una reserva (privado).

    Incluye:
        • cliente
        • sesión
        • timestamps
    """

    id: uuid.UUID
    client_id: uuid.UUID
    class_session_id: uuid.UUID
    created_at: datetime

    client: ClientInBookingResponse
    class_session: ClassSessionInBookingResponse

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquemas compactos para anidamiento
# --------------------------------------------------------------------------- #

class BookingInClientResponse(BookingBase):
    """Versión compacta dentro de Client.

    Evita recursión.
    """

    id: uuid.UUID
    class_session_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingInClassSessionResponse(BookingBase):
    """Versión compacta dentro de ClassSession.

    Evita recursión.
    """

    id: uuid.UUID
    client_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema interno (service → CRUD)
# --------------------------------------------------------------------------- #

class BookingCreateInternal(BaseModel):
    """Esquema interno para crear una reserva después de resolver la lógica de negocio."""  # noqa: E501

    client_id: uuid.UUID
    class_session_id: uuid.UUID
    created_at: datetime
    status: BookingStatus


# --------------------------------------------------------------------------- #
# 6. Versión pública (frontend)
# --------------------------------------------------------------------------- #

class BookingPublic(BaseModel):
    """Versión pública de una reserva.

    Usada en:
        • frontend cliente
        • listados públicos
        • dashboards
    """

    id: uuid.UUID
    status: BookingStatus
    starts_at: datetime
    ends_at: datetime
    gym_class_name: str

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 7. Extensiones públicas
# --------------------------------------------------------------------------- #

class BookingWithSession(BookingPublic):
    """Extiende BookingPublic con datos públicos de la sesión.

    Usado en:
        • /bookings/me
        • front_desk.
    """

    class_session: ClassSessionPublic


class BookingWithClient(BookingPublic):
    """Extiende BookingPublic con datos públicos del cliente.

    Usado en:
        • front_desk
        • dashboards
    """

    client: ClientPublic

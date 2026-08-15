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

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, model_validator

# Importar enums SIEMPRE en runtime (Pydantic v2 los necesita)
from app.core.enums import BookingStatus  # noqa: TC001
from app.schemas.booking_refs import BookingPublic
from app.schemas.class_session import (
    ClassSessionInBookingResponse,
    ClassSessionPublic,
)

# Importar client normalmente (no genera ciclos)
from app.schemas.client import ClientInBookingResponse, ClientPublic  # noqa: TC001

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

    class_session_id: UUID | None = None
    class_schedule_id: UUID | None = None

    @model_validator(mode="after")
    def check_exactly_one_id_is_provided(self) -> BookingCreate:
        """Check un id."""
        has_session_id = self.class_session_id is not None
        has_schedule_id = self.class_schedule_id is not None

        if not (has_session_id ^ has_schedule_id):
            msg = "Debe proporcionar exclusivamente 'class_session_id' o 'class_schedule_id'."
            raise ValueError(msg)
        return self


class BookingUpdate(BaseModel):
    """Esquema para actualizar parcialmente una reserva."""

    status: BookingStatus | None = None
    cancelled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 3. Esquema privado (operativo)
# --------------------------------------------------------------------------- #

class BookingWithRelations(BookingBase):
    """Esquema completo de una reserva (privado).

    Incluye:
        • cliente
        • sesión
        • timestamps
    """

    id: UUID
    client_id: UUID
    class_session_id: UUID
    created_at: datetime

    # Forward refs porque class_session está en TYPE_CHECKING
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

    id: UUID
    class_session_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingInClassSessionResponse(BookingBase):
    """Versión compacta dentro de ClassSession.

    Evita recursión.
    """

    id: UUID
    client_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema interno (service → CRUD)
# --------------------------------------------------------------------------- #

class BookingCreateInternal(BaseModel):
    """Esquema interno para crear una reserva después de resolver la lógica de negocio."""

    client_id: UUID
    class_session_id: UUID
    created_at: datetime
    status: BookingStatus


# --------------------------------------------------------------------------- #
# 6. Versión pública (frontend)
# --------------------------------------------------------------------------- #

# 7. Extensiones públicas
# --------------------------------------------------------------------------- #

class BookingWithSession(BookingPublic):
    """Extiende BookingPublic con datos públicos de la sesión.

    Usado en:
        • /bookings/me
        • front_desk.
    """

    class_session: "ClassSessionPublic"  # noqa: UP037


class BookingWithClient(BookingPublic):
    """Extiende BookingPublic con datos públicos del cliente.

    Usado en:
        • front_desk
        • dashboards
    """

    client: ClientPublic

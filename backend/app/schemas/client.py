"""Schemas para Client (Sprint 6-7).

--------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (Client)
• Esquemas públicos
• Extensiones con bookings, membresía y estadísticas
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

# Evitar circularidad: booking.py importa client.py
if TYPE_CHECKING:

    from app.schemas.booking import BookingPublic

from app.schemas.membership import MembershipPublic  # noqa: TC001
from app.schemas.person import PersonBase, PersonCreate, PersonUpdate

# ruff: noqa: UP037
# --------------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------------- #

class ClientBase(PersonBase):
    """Campos base heredados de PersonBase."""



class ClientCreate(PersonCreate):
    """Datos necesarios para crear un cliente."""



class ClientUpdate(PersonUpdate):
    """Datos necesarios para actualizar un cliente."""


# --------------------------------------------------------------------------- #
# Esquema privado (API interna)
# --------------------------------------------------------------------------- #

class Client(ClientBase):
    """Esquema privado del cliente.

    Incluye relaciones completas para uso interno.
    """

    id: UUID
    bookings: list["BookingPublic"] = Field(default_factory=list)
    membership: MembershipPublic | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Esquema público (frontend)
# --------------------------------------------------------------------------- #

class ClientPublic(BaseModel):
    """Versión pública del cliente.

    Usada en:
        • frontend cliente
        • listados públicos
        • front_desk.
    """

    id: UUID
    full_name: str
    email: str
    phone: str | None = None
    avatar_url: str | None = None
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Cliente con reservas públicas
# --------------------------------------------------------------------------- #

class ClientWithBookings(ClientPublic):
    """Extiende ClientPublic con reservas públicas.

    Usado en:
        • /clients/me/bookings
        • front_desk.
    """

    bookings: list["BookingPublic"] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Cliente con membresía activa
# --------------------------------------------------------------------------- #

class ClientWithMembership(ClientPublic):
    """Extiende ClientPublic con la membresía activa.

    Usado en:
        • /clients/me/membership
        • dashboards operativos.
    """

    membership: MembershipPublic | None = None


# --------------------------------------------------------------------------- #
# Cliente con estadísticas
# --------------------------------------------------------------------------- #

class ClientWithStats(ClientPublic):
    """Extiende ClientPublic con estadísticas básicas.

    Usado en:
        • /clients/me/stats
        • dashboards.
    """

    total_bookings: int
    upcoming_bookings: list["BookingPublic"] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Esquema para respuestas anidadas (ligero)
# --------------------------------------------------------------------------- #

class ClientInBookingResponse(ClientBase):
    """Versión ligera del cliente dentro de Booking.

    No incluye relaciones para evitar recursión.
    """

    id: UUID

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Cliente con actividad completa (dashboard)
# --------------------------------------------------------------------------- #

class ClientWithActivity(ClientPublic):
    """Extiende ClientPublic con información completa de actividad.

    Incluye:
        • reservas del día
        • reservas de la semana
        • reservas futuras
        • reservas pasadas
        • reservas activas
    Usado en:
        • dashboards
        • front_desk
        • perfil cliente
    """

    bookings_today: list["BookingPublic"] = Field(default_factory=list)
    bookings_this_week: list["BookingPublic"] = Field(default_factory=list)
    upcoming_bookings: list["BookingPublic"] = Field(default_factory=list)
    past_bookings: list["BookingPublic"] = Field(default_factory=list)
    active_bookings: list["BookingPublic"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Resolver forward refs
# --------------------------------------------------------------------------- #

Client.model_rebuild()
ClientWithBookings.model_rebuild()
ClientWithStats.model_rebuild()
ClientWithActivity.model_rebuild()

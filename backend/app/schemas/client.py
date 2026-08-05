"""Schemas para Client (Sprint 6-7).

--------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (Client)
• Esquemas públicos
• Extensiones con bookings, membresía y estadísticas
"""
# ruff: noqa: PIE790
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

# Evitamos circularidad
if TYPE_CHECKING:
    import uuid

    from .booking import BookingPublic
    from .membership import MembershipPublic

from .person import PersonBase, PersonCreate, PersonUpdate

# --------------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------------- #

class ClientBase(PersonBase):
    """Campos base heredados de PersonBase."""

    pass


class ClientCreate(PersonCreate):
    """Datos necesarios para crear un cliente."""

    pass


class ClientUpdate(PersonUpdate):
    """Datos necesarios para actualizar un cliente."""

    pass


# --------------------------------------------------------------------------- #
# Esquema privado (API interna)
# --------------------------------------------------------------------------- #

class Client(ClientBase):
    """Esquema privado del cliente.

    Incluye relaciones completas para uso interno.
    """

    id: uuid.UUID
    bookings: list[BookingPublic] = Field(default_factory=list)
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

    id: uuid.UUID
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

    bookings: list[BookingPublic] = Field(default_factory=list)


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
    upcoming_bookings: list[BookingPublic] = Field(default_factory=list)

# --------------------------------------------------------------------------- #
# Esquema para respuestas anidadas (ligero)
# --------------------------------------------------------------------------- #

class ClientInBookingResponse(ClientBase):
    """Versión ligera del cliente dentro de Booking.

    No incluye relaciones para evitar recursión.
    """

    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

# --------------------------------------------------------------------------- #
# 10. Cliente con actividad completa (dashboard)
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

    bookings_today: list[BookingPublic] = Field(default_factory=list)
    bookings_this_week: list[BookingPublic] = Field(default_factory=list)
    upcoming_bookings: list[BookingPublic] = Field(default_factory=list)
    past_bookings: list[BookingPublic] = Field(default_factory=list)
    active_bookings: list[BookingPublic] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

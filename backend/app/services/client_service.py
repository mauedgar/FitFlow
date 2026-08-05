"""Servicios para Client.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con reservas, membresías y estadísticas.
• Actividad del cliente (día, semana, futuras, pasadas).
• Métricas operativas.
• Helpers para frontend y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app import schemas
from app.services.booking_service import to_booking_public

if TYPE_CHECKING:
    from app.models import Booking, Client, Membership


# --------------------------------------------------------------------------- #
# 1. Transformación automática: Client → ClientPublic
# --------------------------------------------------------------------------- #

def to_client_public(client: Client) -> schemas.ClientPublic:
    """Versión pública del cliente."""
    return schemas.ClientPublic(
        id=client.id, # pyright: ignore[reportArgumentType]
        full_name=client.full_name, # pyright: ignore[reportAttributeAccessIssue]
        email=client.user.email, # pyright: ignore[reportArgumentType]
        phone=client.phone, # pyright: ignore[reportAttributeAccessIssue]
        avatar_url=client.avatar_url, # pyright: ignore[reportAttributeAccessIssue]
        created_at=client.created_at, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Extender Client con reservas públicas
# --------------------------------------------------------------------------- #

def to_client_with_bookings(client: Client) -> schemas.ClientWithBookings:
    """Extiende el cliente con sus reservas públicas."""
    bookings = [to_booking_public(b) for b in client.bookings]

    return schemas.ClientWithBookings(
        **to_client_public(client).model_dump(),
        bookings=bookings,
    )


# --------------------------------------------------------------------------- #
# 3. Extender Client con membresía activa
# --------------------------------------------------------------------------- #

def to_client_with_membership(client: Client) -> schemas.ClientWithMembership:
    """Extiende el cliente con su membresía activa."""
    membership: Membership | None = client.membership

    return schemas.ClientWithMembership(
        **to_client_public(client).model_dump(),
        membership=membership, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 4. Actividad del cliente (día, semana, futuras, pasadas)
# --------------------------------------------------------------------------- #

def get_client_bookings_today(client: Client) -> list[Booking]:
    """Devuelve las reservas del cliente correspondientes al día actual."""
    today = datetime.now(tz=timezone.utc).date()
    return [b for b in client.bookings if b.class_session.starts_at.date() == today]


def get_client_bookings_this_week(client: Client) -> list[Booking]:
    """Devuelve las reservas del cliente programadas para los próximos siete días."""
    now = datetime.now(tz=timezone.utc)
    limit = now + timedelta(days=7)
    return [b for b in client.bookings if now < b.class_session.starts_at <= limit] # pyright: ignore[reportGeneralTypeIssues]


def get_client_upcoming_bookings(client: Client) -> list[Booking]:
    """Devuelve todas las reservas futuras del cliente, posteriores a la fecha actual."""
    now = datetime.now(tz=timezone.utc)
    return [b for b in client.bookings if b.class_session.starts_at > now] # pyright: ignore[reportGeneralTypeIssues]


def get_client_past_bookings(client: Client) -> list[Booking]:
    """Devuelve las reservas pasadas del cliente, cuyas sesiones ya finalizaron."""
    now = datetime.now(tz=timezone.utc)
    return [b for b in client.bookings if b.class_session.ends_at < now] # pyright: ignore[reportGeneralTypeIssues]


def get_client_active_bookings(client: Client) -> list[Booking]:
    """Devuelve las reservas que están actualmente en curso."""
    now = datetime.now(tz=timezone.utc)
    return [
        b for b in client.bookings
        if b.class_session.starts_at <= now <= b.class_session.ends_at # pyright: ignore[reportGeneralTypeIssues]
    ]


# --------------------------------------------------------------------------- #
# 5. Métricas del cliente
# --------------------------------------------------------------------------- #

def get_client_total_bookings(client: Client) -> int:
    """Devuelve el número total de reservas realizadas por el cliente."""
    return len(client.bookings)


def get_client_weekly_activity(client: Client) -> int:
    """Devuelve la cantidad de reservas del cliente en la semana actual."""
    return len(get_client_bookings_this_week(client))


def get_client_daily_activity(client: Client) -> int:
    """Devuelve la cantidad de reservas del cliente en el día actual."""
    return len(get_client_bookings_today(client))


# --------------------------------------------------------------------------- #
# 6. Extender Client con estadísticas completas
# --------------------------------------------------------------------------- #

def to_client_with_stats(client: Client) -> schemas.ClientWithStats:
    """Extiende el cliente con estadísticas completas."""
    total_bookings = get_client_total_bookings(client)
    upcoming = get_client_upcoming_bookings(client)

    return schemas.ClientWithStats(
        **to_client_public(client).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=[to_booking_public(b) for b in upcoming],
    )


# --------------------------------------------------------------------------- #
# 7. Extender Client con actividad completa (dashboard)
# --------------------------------------------------------------------------- #

def to_client_with_activity(client: Client) -> schemas.ClientWithActivity:
    """Extiende el cliente con toda su actividad operativa."""
    today = get_client_bookings_today(client)
    week = get_client_bookings_this_week(client)
    upcoming = get_client_upcoming_bookings(client)
    past = get_client_past_bookings(client)
    active = get_client_active_bookings(client)

    return schemas.ClientWithActivity(
        **to_client_public(client).model_dump(),
        bookings_today=[to_booking_public(b) for b in today],
        bookings_this_week=[to_booking_public(b) for b in week],
        upcoming_bookings=[to_booking_public(b) for b in upcoming],
        past_bookings=[to_booking_public(b) for b in past],
        active_bookings=[to_booking_public(b) for b in active],
    )

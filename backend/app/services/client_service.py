"""
Servicios para Client
=====================

Este módulo contiene la lógica de negocio asociada a los perfiles de clientes.
Incluye:

• Transformaciones ORM → Schemas públicos.
• Extensiones con reservas, membresías y estadísticas.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import Client, Membership
from app.services.booking_service import to_booking_public

# --------------------------------------------------------------------------- #
# 1. Transformación automática: Client → ClientPublic
# --------------------------------------------------------------------------- #

def to_client_public(client: Client) -> schemas.ClientPublic:
    """
    Versión pública del cliente.
    Usada en:
        • frontend cliente
        • listados públicos
        • front_desk
    """
    return schemas.ClientPublic(
        id=client.id,
        full_name=client.full_name,
        email=client.user.email,
        phone=client.phone,
        avatar_url=client.avatar_url,
        created_at=client.created_at,
    )


# --------------------------------------------------------------------------- #
# 2. Extender Client con reservas públicas
# --------------------------------------------------------------------------- #

def to_client_with_bookings(client: Client) -> schemas.ClientWithBookings:
    """
    Extiende el cliente con sus reservas públicas.
    Usado en:
        • frontend cliente (mis reservas)
        • front_desk
    """
    bookings = [
        to_booking_public(b)
        for b in client.bookings
    ]

    return schemas.ClientWithBookings(
        **to_client_public(client).model_dump(),
        bookings=bookings,
    )


# --------------------------------------------------------------------------- #
# 3. Extender Client con membresía activa
# --------------------------------------------------------------------------- #

def to_client_with_membership(client: Client) -> schemas.ClientWithMembership:
    """
    Extiende el cliente con su membresía activa.
    Usado en:
        • frontend cliente (mi plan)
        • dashboards operativos
    """
    membership: Membership | None = client.membership

    return schemas.ClientWithMembership(
        **to_client_public(client).model_dump(),
        membership=membership,
    )


# --------------------------------------------------------------------------- #
# 4. Extender Client con estadísticas básicas
# --------------------------------------------------------------------------- #

def to_client_with_stats(client: Client) -> schemas.ClientWithStats:
    """
    Extiende el cliente con estadísticas básicas.
    Usado en:
        • dashboards
        • frontend cliente (actividad)
    """
    total_bookings = len(client.bookings)

    upcoming = [
        b for b in client.bookings
        if b.class_session.starts_at > datetime.now(tz=timezone.utc)
    ]

    return schemas.ClientWithStats(
        **to_client_public(client).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=[to_booking_public(b) for b in upcoming],
    )

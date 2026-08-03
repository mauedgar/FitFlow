"""
Servicios para Membership
=========================

Este módulo contiene la lógica de negocio asociada a las membresías.
Incluye:

• Transformaciones ORM → Schemas públicos.
• Extensiones con cliente y estadísticas.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import Membership
from app.services.client_service import to_client_public

# --------------------------------------------------------------------------- #
# 1. Transformación automática: Membership → MembershipPublic
# --------------------------------------------------------------------------- #

def to_membership_public(m: Membership) -> schemas.MembershipPublic:
    """
    Versión pública de una membresía.
    Usada en:
        • frontend cliente
        • front_desk
        • dashboards
    """
    now = datetime.now(tz=timezone.utc)

    return schemas.MembershipPublic(
        id=m.id,
        plan=m.plan,
        status=m.status,
        start_date=m.start_date,
        end_date=m.end_date,
        is_active=m.status == schemas.MembershipStatus.active,
        is_expired=m.end_date < now,
    )


# --------------------------------------------------------------------------- #
# 2. Extender Membership con datos del cliente
# --------------------------------------------------------------------------- #

def to_membership_with_client(m: Membership) -> schemas.MembershipWithClient:
    """
    Extiende la membresía con datos públicos del cliente.
    Usado en:
        • front_desk
        • dashboards operativos
    """
    return schemas.MembershipWithClient(
        **to_membership_public(m).model_dump(),
        client=to_client_public(m.client),
    )


# --------------------------------------------------------------------------- #
# 3. Extender Membership con estadísticas
# --------------------------------------------------------------------------- #

def to_membership_with_stats(m: Membership) -> schemas.MembershipWithStats:
    """
    Extiende la membresía con estadísticas básicas.
    Usado en:
        • dashboards
        • reportes
    """
    total_bookings = len(m.client.bookings)

    upcoming = [
        b for b in m.client.bookings
        if b.class_session.starts_at > datetime.now(tz=timezone.utc)
    ]

    return schemas.MembershipWithStats(
        **to_membership_public(m).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=[b.id for b in upcoming],
    )

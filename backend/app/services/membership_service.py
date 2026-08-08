"""Servicios para Membership.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con cliente y estadísticas.
• Validaciones de negocio.
• Estado emergente de la membresía.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.enums import MembershipPlan, MembershipStatus
from app.schemas.membership import (
    MembershipPublic,
    MembershipWithClient,
    MembershipWithStats,
)
from app.services.client_service import to_client_public

if TYPE_CHECKING:
    from app.models import Membership


# --------------------------------------------------------------------------- #
# 1. Transformación automática: Membership → MembershipPublic
# --------------------------------------------------------------------------- #

def to_membership_public(m: Membership) -> MembershipPublic:
    """Transforma un modelo ORM Membership en su versión pública."""
    now = datetime.now(tz=timezone.utc)

    return MembershipPublic(
        id=m.id, # pyright: ignore[reportArgumentType]
        plan=m.plan, # pyright: ignore[reportArgumentType]
        status=m.status, # pyright: ignore[reportArgumentType]
        start_date=m.start_date, # pyright: ignore[reportArgumentType]
        end_date=m.end_date, # pyright: ignore[reportArgumentType]
        is_active=m.status == MembershipStatus.active, # pyright: ignore[reportArgumentType]
        is_expired=m.end_date < now, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Validaciones de negocio
# --------------------------------------------------------------------------- #

def validate_membership_active(m: Membership) -> None:
    """Valida que la membresía esté activa."""
    if m.status != MembershipStatus.active: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La membresía no está activa."
        raise ValueError(msg)


def validate_membership_not_expired(m: Membership) -> None:
    """Valida que la membresía no esté vencida."""
    now = datetime.now(tz=timezone.utc)
    if m.end_date < now: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La membresía está vencida."
        raise ValueError(msg)


def validate_membership_access(m: Membership, schedule_plan: MembershipPlan) -> None:
    """Valida si la membresía permite acceder al horario."""
    if schedule_plan is None:
        return

    if m.plan in (MembershipPlan.premium, MembershipPlan.personalized):
        return

    if m.plan != schedule_plan: # pyright: ignore[reportGeneralTypeIssues]
        msg = f"Tu membresía ({m.plan}) no permite acceder a este horario (requiere {schedule_plan})."
        raise ValueError(
            msg,
        )


# --------------------------------------------------------------------------- #
# 3. Extender Membership con datos del cliente
# --------------------------------------------------------------------------- #

def to_membership_with_client(m: Membership) -> MembershipWithClient:
    """Extiende la membresía con datos públicos del cliente."""
    return MembershipWithClient(
        **to_membership_public(m).model_dump(),
        client=to_client_public(m.client),
    )


# --------------------------------------------------------------------------- #
# 4. Extender Membership con estadísticas
# --------------------------------------------------------------------------- #

def to_membership_with_stats(m: Membership) -> MembershipWithStats:
    """Extiende la membresía con estadísticas básicas."""
    total_bookings = len(m.client.bookings)

    upcoming = [
        b for b in m.client.bookings
        if b.class_session.starts_at > datetime.now(tz=timezone.utc) # pyright: ignore[reportGeneralTypeIssues]
    ]

    return MembershipWithStats(
        **to_membership_public(m).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=[b.id for b in upcoming], # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 5. Helpers operativos
# --------------------------------------------------------------------------- #

def is_membership_expiring_soon(m: Membership, days: int = 5) -> bool:
    """Indica si la membresía está por vencer dentro de X días."""
    now = datetime.now(tz=timezone.utc)
    return 0 < (m.end_date - now).days <= days


def is_membership_valid_for_booking(m: Membership) -> bool:
    """Indica si la membresía permite reservar."""
    now = datetime.now(tz=timezone.utc)
    return (
        m.status == MembershipStatus.active
        and m.end_date > now
    ) # pyright: ignore[reportReturnType]

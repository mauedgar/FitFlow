"""
Schemas para Membership (Sprint 6–7)
------------------------------------
Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (Membership)
• Esquemas públicos
• Extensiones con cliente y estadísticas
"""

from __future__ import annotations

from datetime import datetime

# Evitamos circularidad
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..core.enums import MembershipPlan, MembershipStatus

if TYPE_CHECKING:
    from .client import ClientPublic


# --------------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------------- #

class MembershipBase(BaseModel):
    """Campos base de una membresía comercial."""
    plan: MembershipPlan
    status: MembershipStatus
    start_date: datetime
    end_date: datetime
    last_check_in: datetime | None = None
    last_invoice_id: str | None = None


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #

class MembershipCreate(MembershipBase):
    """Datos necesarios para crear una membresía."""
    client_id: UUID


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #

class MembershipUpdate(BaseModel):
    """Datos opcionales para actualizar una membresía."""
    plan: MembershipPlan | None = None
    status: MembershipStatus | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    last_check_in: datetime | None = None
    last_invoice_id: str | None = None


# --------------------------------------------------------------------------- #
# Esquema privado (API interna)
# --------------------------------------------------------------------------- #

class Membership(MembershipBase):
    """
    Esquema privado de membresía.
    Incluye client_id para uso interno.
    """
    id: UUID
    client_id: UUID

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Esquema público (frontend)
# --------------------------------------------------------------------------- #

class MembershipPublic(BaseModel):
    """
    Versión pública de una membresía.
    Usada en:
        • frontend cliente
        • front_desk
        • dashboards
    """
    id: UUID
    plan: MembershipPlan
    status: MembershipStatus
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Membresía con datos del cliente
# --------------------------------------------------------------------------- #

class MembershipWithClient(MembershipPublic):
    """
    Extiende MembershipPublic con datos públicos del cliente.
    Usado en:
        • /memberships/{id}
        • front_desk
        • dashboards operativos
    """
    client: ClientPublic  


# --------------------------------------------------------------------------- #
# Membresía con estadísticas
# --------------------------------------------------------------------------- #

class MembershipWithStats(MembershipPublic):
    """
    Extiende MembershipPublic con estadísticas básicas.
    Usado en:
        • /memberships/stats
        • reportes
    """
    total_bookings: int
    upcoming_bookings: list[UUID] = Field(default_factory=list)

"""Schemas para Membership (Sprint 6-7).

Incluye:
• Esquemas base (crear/actualizar)
• Esquema privado (Membership)
• Esquemas públicos
• Extensiones con cliente y estadísticas
• Esquemas compactos y mini para front desk
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import MembershipPlan, MembershipStatus  # noqa: TC001

# Evitar circularidad: client.py importa membership.py
if TYPE_CHECKING:
    from app.schemas.client import ClientPublic


# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class MembershipBase(BaseModel):
    """Campos base de una membresía comercial."""

    plan: MembershipPlan
    status: MembershipStatus
    start_date: datetime
    end_date: datetime
    last_check_in: datetime | None = None
    last_invoice_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Create
# --------------------------------------------------------------------------- #

class MembershipCreate(MembershipBase):
    """Datos necesarios para crear una membresía."""

    client_id: UUID


# --------------------------------------------------------------------------- #
# 3. Update
# --------------------------------------------------------------------------- #

class MembershipUpdate(BaseModel):
    """Datos opcionales para actualizar una membresía."""

    plan: MembershipPlan | None = None
    status: MembershipStatus | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    last_check_in: datetime | None = None
    last_invoice_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquema privado (API interna)
# --------------------------------------------------------------------------- #

class Membership(MembershipBase):
    """Esquema privado de membresía.

    Incluye client_id para uso interno.
    """

    id: UUID
    client_id: UUID

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema público (frontend)
# --------------------------------------------------------------------------- #

class MembershipPublic(BaseModel):
    """Versión pública de una membresía.

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
# 6. Membresía con datos del cliente
# --------------------------------------------------------------------------- #

class MembershipWithClient(MembershipPublic):
    """Extiende MembershipPublic con datos públicos del cliente."""

    client: "ClientPublic"  # noqa: UP037


# --------------------------------------------------------------------------- #
# 7. Membresía con estadísticas
# --------------------------------------------------------------------------- #

class MembershipWithStats(MembershipPublic):
    """Extiende MembershipPublic con estadísticas básicas."""

    total_bookings: int
    upcoming_bookings: list[UUID] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# 8. Esquema compacto para anidamiento en Client
# --------------------------------------------------------------------------- #

class MembershipInClientResponse(BaseModel):
    """Versión compacta de la membresía dentro del cliente."""

    id: UUID
    plan: MembershipPlan
    status: MembershipStatus
    end_date: datetime
    is_active: bool
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 9. Esquema mini (ultra ligero)
# --------------------------------------------------------------------------- #

class MembershipMini(BaseModel):
    """Versión mínima de la membresía.

    Usado en:
        • front desk
        • dashboards
        • validaciones rápidas
    """

    plan: MembershipPlan
    status: MembershipStatus
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Resolver forward refs
# --------------------------------------------------------------------------- #

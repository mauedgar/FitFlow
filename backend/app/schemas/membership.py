"""
Schemas para Membership (Pydantic v2, Sprint 5)
-----------------------------------------------
• Representa la membresía comercial de un cliente.
• Incluye plan, estado, vigencia y metadatos operativos.
"""

from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict
from app.models.membership import MembershipPlan, MembershipStatus


# ------------------------------------------------------------------ #
# Base
# ------------------------------------------------------------------ #
class MembershipBase(BaseModel):
    plan: MembershipPlan
    status: MembershipStatus
    start_date: datetime
    end_date: datetime
    last_check_in: Optional[datetime] = None
    last_invoice_id: Optional[str] = None


# ------------------------------------------------------------------ #
# Create
# ------------------------------------------------------------------ #
class MembershipCreate(MembershipBase):
    client_id: UUID


# ------------------------------------------------------------------ #
# Update
# ------------------------------------------------------------------ #
class MembershipUpdate(BaseModel):
    plan: Optional[MembershipPlan] = None
    status: Optional[MembershipStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    last_check_in: Optional[datetime] = None
    last_invoice_id: Optional[str] = None


# ------------------------------------------------------------------ #
# Response
# ------------------------------------------------------------------ #
class Membership(MembershipBase):
    id: UUID
    client_id: UUID

    model_config = ConfigDict(from_attributes=True)

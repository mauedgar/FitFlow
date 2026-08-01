# app/schemas/membership.py
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.membership import MembershipPlan

class MembershipBase(BaseModel):
    plan: MembershipPlan
    start_date: datetime
    end_date: datetime

class Membership(MembershipBase):
    id: uuid.UUID
    last_check_in: Optional[datetime]
    last_invoice_id: Optional[str]

    class Config:
        from_attributes = True
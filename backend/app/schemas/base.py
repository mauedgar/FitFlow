# app/schemas/base.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class TimestampSchema(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class SoftDeleteSchema(BaseModel):
    deleted_at: datetime | None = None
    active: bool = True
    model_config = ConfigDict(from_attributes=True)

class IDSchema(BaseModel):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
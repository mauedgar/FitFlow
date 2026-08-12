# app/models/role_permission.py
from sqlalchemy import Column, ForeignKey, Table

from app.db.base_class import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata, # pyright: ignore[reportAttributeAccessIssue]
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

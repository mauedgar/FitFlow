# app/models/role.py
from __future__ import annotations

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Role(Base):
    """Rol del sistema (admin, teacher, client, front_desk)."""

    id = Column(String, primary_key=True)
    description = Column(String, nullable=True)

    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
    )

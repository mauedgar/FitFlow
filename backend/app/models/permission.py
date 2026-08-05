# app/models/permission.py
from __future__ import annotations

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Permission(Base):
    """Permiso granular del sistema (crear clase, cancelar reserva, etc.)."""

    id = Column(String, primary_key=True)
    description = Column(String, nullable=True)

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

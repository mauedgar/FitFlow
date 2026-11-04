"""Schemas para User (Sprint 6-7).

------------------------------
Incluye:
• UserBase
• UserCreate
• UserUpdate
• User (privado)
• UserPublic (público)
• UserWithProfile (extendido)
• UserWithStats (extendido)
"""
# ruff: noqa: UP037
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.enums import UserRole
from pydantic import BaseModel, ConfigDict, EmailStr

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class UserBase(BaseModel):
    """Campos comunes del usuario."""

    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class UserCreate(UserBase):
    """Esquema para crear un usuario."""

    password: str
    role: UserRole | None = UserRole.client


# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class UserUpdate(BaseModel):
    """Esquema para actualizar parcialmente un usuario."""

    email: EmailStr | None = None
    password: str | None = None
    active: bool | None = None
    role: UserRole | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Esquema privado (operativo)
# --------------------------------------------------------------------------- #

class UserInternal(UserBase):
    """Esquema privado del usuario.

    Incluye:
        • timestamps
        • estado activo
        • rol.
    """

    id: UUID
    role: UserRole
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Esquema público
# --------------------------------------------------------------------------- #

class UserPublic(BaseModel):
    """Versión pública del usuario.

    Usada en:
        • /users/me
        • /users/public
        • frontend.
    """

    id: UUID
    email: EmailStr
    role: UserRole
    active: bool

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Usuario con perfil (cliente o profesor)
# --------------------------------------------------------------------------- #

class UserWithProfile(UserPublic):
    """Extiende UserPublic con el perfil asociado.

    • ClientPublic
    • TeacherPublic
    """

    client: "ClientPublic | None" = None
    teacher: "TeacherPublic | None" = None


# --------------------------------------------------------------------------- #
# 7. Usuario con estadísticas
# --------------------------------------------------------------------------- #

class UserWithStats(UserPublic):
    """Extiende UserPublic con estadísticas básicas.

    Usado en:
        • /users/me/stats
        • dashboards.
    """

    total_bookings: int
    upcoming_bookings: int
    total_classes_taught: int | None = None


# --------------------------------------------------------------------------- #
# Resolver forward refs
# --------------------------------------------------------------------------- #

from app.schemas.client import ClientPublic
from app.schemas.teacher import TeacherPublic

UserWithProfile.model_rebuild(
    _types_namespace={"ClientPublic": ClientPublic, "TeacherPublic": TeacherPublic}
)

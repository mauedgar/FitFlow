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
from typing import Literal
from uuid import UUID

from app.core.enums import UserRole
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class UserBase(BaseModel):
    """Campos comunes del usuario."""

    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


def _validate_bcrypt_password(value: str) -> str:
    """Impedir 500 en CRUD por NUL o truncación de nuevas contraseñas."""
    if "\x00" in value:
        raise ValueError("La contraseña contiene un byte NUL no admitido")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("La contraseña excede los 72 bytes admitidos por bcrypt")
    return value


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class UserCreate(UserBase):
    """Esquema para crear un usuario."""

    password: str
    role: UserRole | None = UserRole.client

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


# Public registration is never an administrative provisioning surface.
class PublicUserRegistration(UserBase):
    """Only client accounts may be created without authentication."""

    password: str
    role: Literal[UserRole.client] = UserRole.client

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


# --------------------------------------------------------------------------- #
# 3. Actualización
# --------------------------------------------------------------------------- #

class UserUpdate(BaseModel):
    """Esquema para actualizar parcialmente un usuario."""

    email: EmailStr | None = None
    password: str | None = None
    active: bool | None = None
    role: UserRole | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        return _validate_bcrypt_password(value) if value is not None else None

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

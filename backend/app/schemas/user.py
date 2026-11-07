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

from datetime import datetime  # noqa: TC003
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import UserRole

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

def _validate_bcrypt_password(value: str) -> str:
    """Reject unsafe new hashes; legacy password verification remains unchanged."""
    if "\x00" in value:
        raise ValueError("La contraseña contiene un byte NUL no admitido")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("La contraseña excede los 72 bytes admitidos por bcrypt")
    return value


class UserCreate(UserBase):
    """Esquema para crear un usuario."""

    password: str
    role: UserRole | None = UserRole.client

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


class PublicUserRegistration(UserBase):
    """Only the fields accepted from an unauthenticated self-registration.

    Privileged roles belong to trusted internal provisioning, never the
    public request. Preserve the currently accepted legacy full_name field
    without treating it as a persisted Client/Person profile.
    """

    password: str
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


class PublicClientRegistration(UserBase):
    """Public signup preserves given and compound family names explicitly."""

    password: str
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_bcrypt_password(value)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_personal_name(cls, value: object) -> object:
        return " ".join(value.split()) if isinstance(value, str) else value


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

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        return _validate_bcrypt_password(value) if value is not None else None


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

from app.schemas.client import ClientPublic  # noqa: E402
from app.schemas.teacher import TeacherPublic  # noqa: E402

UserWithProfile.model_rebuild(
    _types_namespace={"ClientPublic": ClientPublic, "TeacherPublic": TeacherPublic}
)

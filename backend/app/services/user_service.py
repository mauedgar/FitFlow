"""Servicios para User.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con perfil (cliente o profesor).
• Extensiones con estadísticas completas.
• Actividad del usuario.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.services.client_service import (
    get_client_total_bookings,
    get_client_upcoming_bookings,
    to_client_public,
)
from app.services.teacher_service import to_teacher_public
from app.schemas.user import UserPublic, UserWithProfile, UserWithStats

if TYPE_CHECKING:
    from app.db.models import User


# --------------------------------------------------------------------------- #
# 1. Transformación automática: User → UserPublic
# --------------------------------------------------------------------------- #

def to_user_public(user: User) -> UserPublic:
    """Versión pública del usuario."""
    return UserPublic(
        id=user.id, # pyright: ignore[reportArgumentType]
        email=user.email, # pyright: ignore[reportArgumentType]
        role=user.role, # pyright: ignore[reportArgumentType]
        active=user.active, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Extender User con su perfil (cliente o profesor)
# --------------------------------------------------------------------------- #

def to_user_with_profile(user: User) -> UserWithProfile:
    """Extiende el usuario con su perfil asociado."""
    client_public = None
    teacher_public = None

    if user.person_profile and hasattr(user.person_profile, "client"):
        client_public = to_client_public(user.person_profile.client) # pyright: ignore[reportAttributeAccessIssue]

    if user.person_profile and hasattr(user.person_profile, "teacher"):
        teacher_public = to_teacher_public(user.person_profile.teacher) # pyright: ignore[reportAttributeAccessIssue]

    return UserWithProfile(
        **to_user_public(user).model_dump(),
        client=client_public,
        teacher=teacher_public,
    )


# --------------------------------------------------------------------------- #
# 3. Extender User con estadísticas completas
# --------------------------------------------------------------------------- #

def to_user_with_stats(user: User) -> UserWithStats:
    """Extiende el usuario con estadísticas completas."""
    now = datetime.now(tz=timezone.utc)  # noqa: F841

    total_bookings = 0
    upcoming_bookings = 0
    total_classes_taught = 0

    if user.person_profile and hasattr(user.person_profile, "client"):
        client = user.person_profile.client # pyright: ignore[reportAttributeAccessIssue]
        total_bookings = get_client_total_bookings(client)
        upcoming_bookings = len(get_client_upcoming_bookings(client))

    if user.person_profile and hasattr(user.person_profile, "teacher"):
        teacher = user.person_profile.teacher # pyright: ignore[reportAttributeAccessIssue]
        total_classes_taught = len(teacher.class_schedules)

    return UserWithStats(
        **to_user_public(user).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=upcoming_bookings,
        total_classes_taught=total_classes_taught,
    )

"""
Servicios para User (Sprint 6–7)
================================

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con perfil (cliente o profesor).
• Extensiones con estadísticas básicas.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import User
from app.services.client_service import to_client_public
from app.services.teacher_service import to_teacher_public

# --------------------------------------------------------------------------- #
# 1. Transformación automática: User → UserPublic
# --------------------------------------------------------------------------- #

def to_user_public(user: User) -> schemas.UserPublic:
    """
    Versión pública del usuario.
    Usada en:
        • frontend
        • listados públicos
        • dashboards
    """
    return schemas.UserPublic(
        id=user.id,
        email=user.email,
        role=user.role,
        active=user.active,
    )


# --------------------------------------------------------------------------- #
# 2. Extender User con su perfil (cliente o profesor)
# --------------------------------------------------------------------------- #

def to_user_with_profile(user: User) -> schemas.UserWithProfile:
    """
    Extiende el usuario con su perfil asociado:
        • ClientPublic
        • TeacherPublic
    Usado en:
        • /users/me
        • frontend
        • dashboards
    """
    client_public = None
    teacher_public = None

    # Perfil cliente
    if user.person_profile and hasattr(user.person_profile, "client"):
        client_public = to_client_public(user.person_profile.client)

    # Perfil profesor
    if user.person_profile and hasattr(user.person_profile, "teacher"):
        teacher_public = to_teacher_public(user.person_profile.teacher)

    return schemas.UserWithProfile(
        **to_user_public(user).model_dump(),
        client=client_public,
        teacher=teacher_public,
    )


# --------------------------------------------------------------------------- #
# 3. Extender User con estadísticas básicas
# --------------------------------------------------------------------------- #

def to_user_with_stats(user: User) -> schemas.UserWithStats:
    """
    Extiende el usuario con estadísticas básicas.
    Usado en:
        • /users/me/stats
        • dashboards
    """
    now = datetime.now(tz=timezone.utc)

    total_bookings = 0
    upcoming_bookings = 0
    total_classes_taught = 0

    # Si es cliente
    if user.person_profile and hasattr(user.person_profile, "client"):
        client = user.person_profile.client
        total_bookings = len(client.bookings)
        upcoming_bookings = len([
            b for b in client.bookings
            if b.class_session.starts_at > now
        ])

    # Si es profesor
    if user.person_profile and hasattr(user.person_profile, "teacher"):
        teacher = user.person_profile.teacher
        total_classes_taught = len(teacher.class_schedules)

    return schemas.UserWithStats(
        **to_user_public(user).model_dump(),
        total_bookings=total_bookings,
        upcoming_bookings=upcoming_bookings,
        total_classes_taught=total_classes_taught,
    )

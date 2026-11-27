"""Servicios para User.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con perfil (cliente o profesor).
• Extensiones con estadísticas completas.
• Actividad del usuario.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.crud_user import user as user_crud
from app.db.models.booking import Booking
from app.db.models.client import Client
from app.db.models.teacher import Teacher
from app.schemas.user import UserPublic, UserWithProfile, UserWithStats
from app.services.client_service import (
    get_client_total_bookings,
    get_client_upcoming_bookings,
    to_client_public,
)
from app.services.teacher_service import to_teacher_public

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

async def to_user_with_profile(db: AsyncSession, user: User) -> UserWithProfile:
    """Resolve only profiles owned by this authenticated User."""
    client = await db.scalar(
        select(Client).where(
            Client.user_id == user.id, Client.deleted_at.is_(None),
        ).options(selectinload(Client.user))
    )
    teacher = await db.scalar(
        select(Teacher).where(
            Teacher.user_id == user.id, Teacher.deleted_at.is_(None),
        )
    )
    return UserWithProfile(
        **to_user_public(user).model_dump(),
        client=to_client_public(client) if client is not None else None,
        teacher=to_teacher_public(teacher) if teacher is not None else None,
    )


# --------------------------------------------------------------------------- #
# 3. Extender User con estadísticas completas
# --------------------------------------------------------------------------- #

async def to_user_with_stats(db: AsyncSession, user: User) -> UserWithStats:
    """Load the exact owned profile and required relations, never lazy IO."""
    client = await db.scalar(
        select(Client).where(
            Client.user_id == user.id, Client.deleted_at.is_(None),
        ).options(selectinload(Client.bookings).selectinload(Booking.class_session))
    )
    teacher = await db.scalar(
        select(Teacher).where(
            Teacher.user_id == user.id, Teacher.deleted_at.is_(None),
        ).options(selectinload(Teacher.class_schedules))
    )
    return UserWithStats(
        **to_user_public(user).model_dump(),
        total_bookings=get_client_total_bookings(client) if client is not None else 0,
        upcoming_bookings=len(get_client_upcoming_bookings(client)) if client is not None else 0,
        total_classes_taught=len(teacher.class_schedules) if teacher is not None else 0,
    )


async def get_by_email(
    email: str, db: "AsyncSession | None" = None, include_relations: bool = False,
) -> User | None:
  if db is None:
    # Handle the case where db session is not provided, or raise an error/get a session
    msg = "A database session 'db' is required."
    raise ValueError(msg)
  return await user_crud.get_by_email(
      db, email=email, include_relations=include_relations,
  )

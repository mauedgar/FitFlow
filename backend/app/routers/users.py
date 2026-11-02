"""Router User (Sprint 6-7).

-----------------------------------------
• Registro y gestión de usuarios.
• Endpoints públicos y privados.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
• Compatible con TanStack Query.
• Sin SQLAlchemy directo.
"""

from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID

from app.core.deps import get_current_user
from app.core.enums import UserRole
from app.crud.crud_user import user as user_crud
from app.db.models import Booking, Client, Teacher
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.user import (
    PublicUserRegistration,
    UserCreate,
    UserPublic,
    UserWithProfile,
    UserWithStats,
)
from app.services.user_service import (
    to_user_public,
    to_user_with_profile,
    to_user_with_stats,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/users", tags=["users"])


def _is_email_unique_violation(exc: IntegrityError) -> bool:
    """Only map the known email index violation to the duplicate-email response."""
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if sqlstate != "23505":
        return False

    # asyncpg's native cause exposes constraint_name; its SQLAlchemy adapter
    # may only surface it in the stable PostgreSQL diagnostic message.
    cause = getattr(orig, "__cause__", None)
    constraint_name = getattr(orig, "constraint_name", None) or getattr(
        cause, "constraint_name", None
    )
    if constraint_name is None:
        match = re.search(r'unique constraint "([^"]+)"', str(orig))
        constraint_name = match.group(1) if match else None
    return constraint_name == "ix_users_email"


# --------------------------------------------------------------------------- #
# Registrar usuario
# --------------------------------------------------------------------------- #
@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    *,
    user_in: PublicUserRegistration,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserPublic:
    """Registra un nuevo usuario en el sistema.

    Reglas:
        • El email debe ser único.
        • La contraseña se hashea automáticamente.
        • El rol por defecto es CLIENT.
    """
    existing = await user_crud.get_by_email(
        db=db, email=user_in.email, include_deleted=True
    )
    if existing:
        raise HTTPException(400, "El email ya está registrado.")

    try:
        # Never persist caller-supplied role from an unauthenticated request.
        public_account = UserCreate(
            email=user_in.email, password=user_in.password, role=UserRole.client,
        )
        user = await user_crud.create(db=db, obj_in=public_account)
    except IntegrityError as exc:
        # A concurrent registration can pass the precheck; UNIQUE remains SOT.
        await db.rollback()
        if _is_email_unique_violation(exc):
            raise HTTPException(400, "El email ya está registrado.") from exc
        raise
    return to_user_public(user)


# --------------------------------------------------------------------------- #
# Listado público de usuarios
# --------------------------------------------------------------------------- #
@router.get("/public", response_model=list[UserPublic])
async def list_public_users(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[UserPublic]:
    """Lista usuarios en versión pública."""
    users = await user_crud.get_multi(db=db)
    return [to_user_public(u) for u in users]


# --------------------------------------------------------------------------- #
# Usuario público por ID
# --------------------------------------------------------------------------- #
@router.get("/{user_id}/public", response_model=UserPublic)
async def read_public_user(
    *,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserPublic:
    """Obtiene un usuario en versión pública."""
    user = await user_crud.get(db=db, obj_id=user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")

    return to_user_public(user)


async def _get_authenticated_self_with_relations(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    principal: Annotated[User, Depends(get_current_user)],
) -> User:
    """Load only the JWT subject's ORM account and bounded profile relations.

    The public /me paths have no user_id; no caller-controlled identity is used.
    Explicit queries also satisfy ORM relationships configured with lazy='raise'.
    """
    user = await db.scalar(
        select(User)
        .where(User.id == principal.id)
        .options(selectinload(User.person_profile))
    )
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    profile = user.person_profile
    if isinstance(profile, Client):
        # The polymorphic identity map keeps the same profile instance.
        # The public projection needs Client.user; stats need bookings/sessions.
        await db.scalar(
            select(Client)
            .where(Client.id == profile.id)
            .options(
                selectinload(Client.user),
                selectinload(Client.bookings).selectinload(Booking.class_session),
            )
        )
    elif isinstance(profile, Teacher):
        await db.scalar(
            select(Teacher)
            .where(Teacher.id == profile.id)
            .options(selectinload(Teacher.class_schedules))
        )
    return user


# --------------------------------------------------------------------------- #
# Perfil del usuario actual
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=UserWithProfile)
async def read_my_profile(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_get_authenticated_self_with_relations)],
) -> UserWithProfile:
    """Devuelve el perfil del usuario actual.

    Incluye:
        • datos públicos
        • perfil asociado (cliente o profesor)
    """
    return to_user_with_profile(current_user)


# --------------------------------------------------------------------------- #
# Estadísticas del usuario actual
# --------------------------------------------------------------------------- #
@router.get("/me/stats", response_model=UserWithStats)
async def read_my_stats(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_get_authenticated_self_with_relations)],
) -> UserWithStats:
    """Devuelve estadísticas básicas del usuario actual.

    Incluye:
        • total de reservas (si es cliente)
        • reservas futuras (si es cliente)
        • clases dictadas (si es profesor)
    """
    return to_user_with_stats(current_user)

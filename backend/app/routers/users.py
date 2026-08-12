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

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_admin_or_self_guard
from app.db.session import get_async_session
from app.services.user_service import (
    to_user_public,
    to_user_with_profile,
    to_user_with_stats,
)
from app.schemas.user import (
    UserCreate,
    UserPublic,
    UserWithProfile,
    UserWithStats,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

from app.crud.crud_user import user_crud

router = APIRouter(prefix="/users", tags=["users"])


# --------------------------------------------------------------------------- #
# Registrar usuario
# --------------------------------------------------------------------------- #
@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    *,
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserPublic:
    """Registra un nuevo usuario en el sistema.

    Reglas:
        • El email debe ser único.
        • La contraseña se hashea automáticamente.
        • El rol por defecto es CLIENT.
    """
    existing = await user_crud.get_by_email(db=db, email=user_in.email)
    if existing:
        raise HTTPException(400, "El email ya está registrado.")

    user = await user_crud.create(db=db, obj_in=user_in)
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


# --------------------------------------------------------------------------- #
# Perfil del usuario actual
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=UserWithProfile)
async def read_my_profile(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],  # noqa: ARG001
    current_user: Annotated[User, Depends(require_admin_or_self_guard)],
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
    db: Annotated[AsyncSession, Depends(get_async_session)],  # noqa: ARG001
    current_user: Annotated[User, Depends(require_admin_or_self_guard)],
) -> UserWithStats:
    """Devuelve estadísticas básicas del usuario actual.

    Incluye:
        • total de reservas (si es cliente)
        • reservas futuras (si es cliente)
        • clases dictadas (si es profesor)
    """
    return to_user_with_stats(current_user)

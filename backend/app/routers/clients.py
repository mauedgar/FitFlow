"""Router Client (Sprint 6-7).

-----------------------------------------
• CRUD de perfiles de clientes.
• Endpoints públicos y privados.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
• Compatible con TanStack Query.
• Sin SQLAlchemy directo.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    require_admin,
    require_admin_or_client,
    require_client,
    require_current_user,
    oauth2_scheme,
)
from app.core.enums import UserRole
from app.crud.crud_client import client
from app.db.models.client import Client
from app.crud.crud_user import user as user_crud
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.client import (
    ClientCreate,
    ClientPublic,
    ClientUpdate,
    ClientWithActivity,
    ClientWithBookings,
    ClientWithMembership,
    ClientWithRelations,
    ClientWithStats,
)
from app.schemas.user import UserPublic
from app.services.errors import AuthError, PermissionDeniedError
from app.services.client_service import (
    to_client_public,
    to_client_with_relations,
    to_client_with_activity,
    to_client_with_bookings,
    to_client_with_membership,
    to_client_with_stats,
)

# ruff: noqa: ARG001

router = APIRouter(prefix="/clients", tags=["clients"])


async def _require_clients_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserPublic:
    """Preserve HTTP 401 semantics for invalid/expired/missing JWT identities."""
    try:
        return await require_current_user(db=db, token=token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def _require_clients_admin(
    user: Annotated[UserPublic, Depends(_require_clients_current_user)],
) -> UserPublic:
    """Translate the existing role guard at this HTTP boundary."""
    try:
        return await require_admin(user)
    except PermissionDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


async def _require_clients_client(
    user: Annotated[UserPublic, Depends(_require_clients_current_user)],
) -> UserPublic:
    """Only clients have a current-client profile."""
    try:
        return await require_client(user)
    except PermissionDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


async def _require_clients_admin_or_client(
    user: Annotated[UserPublic, Depends(_require_clients_current_user)],
) -> UserPublic:
    """Deny other roles before evaluating profile ownership."""
    try:
        return await require_admin_or_client(user)
    except PermissionDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


def _require_admin_or_owner(user: User, client_profile: Client) -> None:
    """Compare an account ID with the profile's user_id, not its person ID."""
    if user.role != UserRole.admin and user.id != client_profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado.",
        )


# --------------------------------------------------------------------------- #
# Crear Client para un User existente
# --------------------------------------------------------------------------- #
@router.post("/{user_id}", response_model=ClientWithRelations, status_code=status.HTTP_201_CREATED)
async def create_client_for_user(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: UUID,
    client_in: ClientCreate,
    current_user: Annotated[User, Depends(_require_clients_admin)],
) -> ClientWithRelations:
    """Crea un perfil de cliente para un usuario existente."""
    user = await user_crud.get(db=db, obj_id=user_id, include_relations=True)
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")

    if user.person_profile:
        raise HTTPException(400, "El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.client: # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(400, "El usuario no tiene rol CLIENT.")

    client_ = await client.create_with_user(db=db, obj_in=client_in, user=user)
    created = await client.get_with_relations(db=db, client_id=client_.id)
    if created is None:
        raise HTTPException(404, "Cliente no encontrado.")
    return to_client_with_relations(created)


# --------------------------------------------------------------------------- #
# Listar Clients (admin)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[ClientPublic])
async def read_clients(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(_require_clients_admin)],
) -> list[ClientPublic]:
    """Lista clientes en versión pública (admin)."""
    clients = await client.get_multi_visible(db=db, skip=skip, limit=limit)
    return [to_client_public(c) for c in clients]


# --------------------------------------------------------------------------- #
# Perfil del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=ClientPublic)
async def read_my_profile(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_require_clients_client)],
) -> ClientPublic:
    """Devuelve el perfil público del cliente actual."""
    client_ = await client.get_by_user_id(db=db, user_id=current_user.id) # pyright: ignore[reportArgumentType]
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_public(client_)


# --------------------------------------------------------------------------- #
# Reservas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/bookings", response_model=ClientWithBookings)
async def read_my_bookings(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_require_clients_client)],
) -> ClientWithBookings:
    """Devuelve el perfil del cliente con sus reservas públicas."""
    client_ = await client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_bookings(client_)


# --------------------------------------------------------------------------- #
# Membresía del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/membership", response_model=ClientWithMembership)
async def read_my_membership(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_require_clients_client)],
) -> ClientWithMembership:
    """Devuelve el perfil del cliente con su membresía activa."""
    client_ = await client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_membership(client_)


# --------------------------------------------------------------------------- #
# Estadísticas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/stats", response_model=ClientWithStats)
async def read_my_stats(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_require_clients_client)],
) -> ClientWithStats:
    """Devuelve estadísticas básicas del cliente."""
    client_ = await client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_stats(client_)


# --------------------------------------------------------------------------- #
# Actividad completa del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/activity", response_model=ClientWithActivity)
async def read_my_activity(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(_require_clients_client)],
) -> ClientWithActivity:
    """Devuelve la actividad completa del cliente."""
    client_ = await client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_activity(client_)


# --------------------------------------------------------------------------- #
# Obtener Client por ID (privado)
# --------------------------------------------------------------------------- #
@router.get("/{client_id}", response_model=ClientWithRelations)
async def read_client_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    current_user: Annotated[User, Depends(_require_clients_admin_or_client)],
) -> ClientWithRelations:
    """Obtiene detalles privados de un cliente."""
    client_ = await client.get_with_relations(db=db, client_id=client_id)
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    _require_admin_or_owner(current_user, client_)
    return to_client_with_relations(client_)


# --------------------------------------------------------------------------- #
# Actualizar Client
# --------------------------------------------------------------------------- #
@router.put("/{client_id}", response_model=ClientWithRelations)
async def update_client(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    client_in: ClientUpdate,
    current_user: Annotated[User, Depends(_require_clients_admin_or_client)],
) -> ClientWithRelations:
    """Actualiza el perfil privado del cliente."""
    client_ = await client.get(db=db, obj_id=client_id)
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    _require_admin_or_owner(current_user, client_)
    await client.update(db=db, db_obj=client_, obj_in=client_in)
    refreshed = await client.get_with_relations(db=db, client_id=client_id)
    if refreshed is None:
        raise HTTPException(404, "Cliente no encontrado.")
    return to_client_with_relations(refreshed)


# --------------------------------------------------------------------------- #
# Eliminar Client
# --------------------------------------------------------------------------- #
@router.delete("/{client_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_client(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    current_user: Annotated[User, Depends(_require_clients_admin)],
) -> dict[str, str]:
    """Elimina un perfil de cliente y desasocia el perfil Person del User."""
    client_ = await client.get(db=db, obj_id=client_id)
    if not client_:
        raise HTTPException(404, "Cliente no encontrado.")

    await client.remove(db=db, db_obj=client_)

    return {"message": "Perfil de cliente desactivado exitosamente."}

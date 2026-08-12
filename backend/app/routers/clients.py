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

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app import crud
from app.core.deps import (
    require_admin,
    require_admin_client_or_self,
    require_admin_or_self_guard,
)
from app.crud.crud_user import user_crud
from app.db.session import get_async_session
from backend.app.db.models.user import User, UserRole
from app.services.client_service import (
    to_client_public,
    to_client_with_activity,
    to_client_with_bookings,
    to_client_with_membership,
    to_client_with_stats,
    unlink_user_profile,
)
from app.schemas.client import (
    Client,
    ClientCreate,
    ClientPublic,
    ClientUpdate,
    ClientWithActivity,
    ClientWithBookings,
    ClientWithMembership,
    ClientWithStats,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
# ruff: noqa: ARG001

router = APIRouter(prefix="/clients", tags=["clients"])


# --------------------------------------------------------------------------- #
# Crear Client para un User existente
# --------------------------------------------------------------------------- #
@router.post("/{user_id}", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client_for_user(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: UUID,
    client_in: ClientCreate,
    current_user: Annotated[User, Depends(require_admin)],
) -> Client:
    """Crea un perfil de cliente para un usuario existente."""
    user = await user_crud.get(db=db, obj_id=user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")

    if user.person_profile:
        raise HTTPException(400, "El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.client: # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(400, "El usuario no tiene rol CLIENT.")

    client = await crud.client.create_with_user(db=db, obj_in=client_in, user=user)
    return Client.model_validate(client)


# --------------------------------------------------------------------------- #
# Listar Clients (admin)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[ClientPublic])
async def read_clients(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(require_admin)],
) -> list[ClientPublic]:
    """Lista clientes en versión pública (admin)."""
    clients = await crud.client.get_multi(db=db, skip=skip, limit=limit)
    return [to_client_public(c) for c in clients]


# --------------------------------------------------------------------------- #
# Obtener Client por ID (privado)
# --------------------------------------------------------------------------- #
@router.get("/{client_id}", response_model=Client)
async def read_client_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    current_user: Annotated[User, Depends(require_admin_or_self_guard)],
) -> Client:
    """Obtiene detalles privados de un cliente."""
    client = await crud.client.get(db=db, obj_id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return Client.model_validate(client)


# --------------------------------------------------------------------------- #
# Perfil del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=ClientPublic)
async def read_my_profile(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> ClientPublic:
    """Devuelve el perfil público del cliente actual."""
    client = await crud.client.get_by_user_id(db=db, user_id=current_user.id) # pyright: ignore[reportArgumentType]
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_public(client)


# --------------------------------------------------------------------------- #
# Reservas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/bookings", response_model=ClientWithBookings)
async def read_my_bookings(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> ClientWithBookings:
    """Devuelve el perfil del cliente con sus reservas públicas."""
    client = await crud.client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_bookings(client)


# --------------------------------------------------------------------------- #
# Membresía del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/membership", response_model=ClientWithMembership)
async def read_my_membership(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> ClientWithMembership:
    """Devuelve el perfil del cliente con su membresía activa."""
    client = await crud.client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_membership(client)


# --------------------------------------------------------------------------- #
# Estadísticas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/stats", response_model=ClientWithStats)
async def read_my_stats(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> ClientWithStats:
    """Devuelve estadísticas básicas del cliente."""
    client = await crud.client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_stats(client)


# --------------------------------------------------------------------------- #
# Actividad completa del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/activity", response_model=ClientWithActivity)
async def read_my_activity(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> ClientWithActivity:
    """Devuelve la actividad completa del cliente."""
    client = await crud.client.get_by_user_id(
        db=db,
        user_id=current_user.id, # pyright: ignore[reportArgumentType]
        include_relations=True,
    )
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return to_client_with_activity(client)


# --------------------------------------------------------------------------- #
# Actualizar Client
# --------------------------------------------------------------------------- #
@router.put("/{client_id}", response_model=Client)
async def update_client(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    client_in: ClientUpdate,
    current_user: Annotated[User, Depends(require_admin_client_or_self)],
) -> Client:
    """Actualiza el perfil privado del cliente."""
    client = await crud.client.get(db=db, obj_id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    updated = await crud.client.update(db=db, db_obj=client, obj_in=client_in)
    return Client.model_validate(updated)


# --------------------------------------------------------------------------- #
# Eliminar Client
# --------------------------------------------------------------------------- #
@router.delete("/{client_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_client(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    client_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
) -> dict[str, str]:
    """Elimina un perfil de cliente y desasocia el perfil Person del User."""
    client = await crud.client.get(db=db, obj_id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    await unlink_user_profile(db=db, client=client)
    await crud.client.remove(db=db, db_obj=client)

    return {"message": "Perfil de cliente eliminado exitosamente."}

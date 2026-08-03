"""
Router Client (Sprint 6–7)
--------------------------
• CRUD de perfiles de clientes.
• Endpoints públicos y privados.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""
# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID

from app import crud, schemas
from app.api.deps import (
    require_admin,
    require_admin_client_or_self,
    require_admin_or_self_guard,
)
from app.db.session import get_async_session
from app.models.user import User, UserRole
from app.services.client_service import (
    to_client_public,
    to_client_with_bookings,
    to_client_with_membership,
    to_client_with_stats,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/clients", tags=["clients"])


# --------------------------------------------------------------------------- #
# Crear Client para un User existente
# --------------------------------------------------------------------------- #
@router.post("/{user_id}", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
async def create_client_for_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: UUID,
    client_in: schemas.ClientCreate,
    current_user: User = Depends(require_admin),
):
    """Crea un perfil de cliente para un usuario existente."""
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")

    if user.person_profile:
        raise HTTPException(400, "El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.client:
        raise HTTPException(400, "El usuario no tiene rol CLIENT.")

    client = await crud.client.create_with_user(db=db, obj_in=client_in, user=user)
    return client


# --------------------------------------------------------------------------- #
# Listar Clients (admin)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[schemas.ClientPublic])
async def read_clients(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
):
    """Lista clientes en versión pública."""
    clients = await crud.client.get_multi(db, skip=skip, limit=limit)
    return [to_client_public(c) for c in clients]


# --------------------------------------------------------------------------- #
# Obtener Client por ID (privado)
# --------------------------------------------------------------------------- #
@router.get("/{client_id}", response_model=schemas.Client)
async def read_client_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    current_user: User = Depends(require_admin_or_self_guard),
):
    """Obtiene detalles privados de un cliente."""
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    return client


# --------------------------------------------------------------------------- #
# Perfil del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=schemas.ClientPublic)
async def read_my_profile(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_client_or_self),
):
    """Devuelve el perfil público del cliente actual."""
    client = current_user.person_profile.client
    return to_client_public(client)


# --------------------------------------------------------------------------- #
# Reservas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/bookings", response_model=schemas.ClientWithBookings)
async def read_my_bookings(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_client_or_self),
):
    """Devuelve el perfil del cliente con sus reservas públicas."""
    client = await crud.client.get(
        db,
        id=current_user.person_profile.client.id,
        include_relations=True,
    )
    return to_client_with_bookings(client)


# --------------------------------------------------------------------------- #
# Membresía del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/membership", response_model=schemas.ClientWithMembership)
async def read_my_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_client_or_self),
):
    """Devuelve el perfil del cliente con su membresía activa."""
    client = await crud.client.get(
        db,
        id=current_user.person_profile.client.id,
        include_relations=True,
    )
    return to_client_with_membership(client)


# --------------------------------------------------------------------------- #
# Estadísticas del cliente actual (público)
# --------------------------------------------------------------------------- #
@router.get("/me/stats", response_model=schemas.ClientWithStats)
async def read_my_stats(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_client_or_self),
):
    """Devuelve estadísticas básicas del cliente."""
    client = await crud.client.get(
        db,
        id=current_user.person_profile.client.id,
        include_relations=True,
    )
    return to_client_with_stats(client)


# --------------------------------------------------------------------------- #
# Actualizar Client
# --------------------------------------------------------------------------- #
@router.put("/{client_id}", response_model=schemas.Client)
async def update_client(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    client_in: schemas.ClientUpdate,
    current_user: User = Depends(require_admin_client_or_self),
):
    """Actualiza el perfil privado del cliente."""
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    updated = await crud.client.update(db, db_obj=client, obj_in=client_in)
    return updated


# --------------------------------------------------------------------------- #
# Eliminar Client
# --------------------------------------------------------------------------- #
@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    current_user: User = Depends(require_admin),
):
    """Elimina un perfil de cliente."""
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    # Desasociar Person → User
    user = await crud.user.get(db, id=client.user.id)
    if user:
        user.person_profile = None
        db.add(user)
        await db.commit()

    await crud.client.remove(db, id=client_id)
    return {"message": "Perfil de cliente eliminado exitosamente."}

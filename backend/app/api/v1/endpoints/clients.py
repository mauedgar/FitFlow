"""
Endpoints para Client (asíncrono, Sprint 5)
-------------------------------------------
• CRUD completo para perfiles de clientes.
• Validación estricta de roles (admin / self).
• Uso de AsyncSession + select() + selectinload().
"""

from __future__ import annotations
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app import crud, schemas
from app.models import Client, User, UserRole
from app.api.deps import (
    get_current_active_user,
    get_current_admin,
    get_admin_or_self,
)

router = APIRouter(prefix="/clients", tags=["clients"])


# ------------------------------------------------------------------ #
# Crear Client para un User existente
# ------------------------------------------------------------------ #
@router.post("/{user_id}", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
async def create_client_for_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: UUID,
    client_in: schemas.ClientCreate,
    current_user: User = Depends(get_current_admin),
):
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user.person_profile:
        raise HTTPException(status_code=400, detail="El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario no tiene rol '{UserRole.CLIENT}'. Actualiza el rol primero.",
        )

    client = await crud.client.create_with_user(db=db, obj_in=client_in, user=user)
    return client


# ------------------------------------------------------------------ #
# Listar Clients
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Client])
async def read_clients(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
):
    stmt = (
        await crud.client.get_multi(db, skip=skip, limit=limit)
    )
    return stmt


# ------------------------------------------------------------------ #
# Obtener Client por ID
# ------------------------------------------------------------------ #
@router.get("/{client_id}", response_model=schemas.Client)
async def read_client_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    current_user: User = Depends(get_admin_or_self),
):
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    return client


# ------------------------------------------------------------------ #
# Actualizar Client
# ------------------------------------------------------------------ #
@router.put("/{client_id}", response_model=schemas.Client)
async def update_client(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    client_in: schemas.ClientUpdate,
    current_user: User = Depends(get_current_active_user),
):
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # Autorización: admin o el propio cliente
    if current_user.role != UserRole.ADMIN:
        if not current_user.person_profile or current_user.person_profile.id != client_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este perfil.")

    updated = await crud.client.update(db, db_obj=client, obj_in=client_in)
    return updated


# ------------------------------------------------------------------ #
# Eliminar Client
# ------------------------------------------------------------------ #
@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    *,
    db: AsyncSession = Depends(get_async_session),
    client_id: UUID,
    current_user: User = Depends(get_current_admin),
):
    client = await crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    user = await crud.user.get(db, id=client.user.id)
    if user:
        user.person_profile_id = None
        db.add(user)
        await db.commit()

    await crud.client.remove(db, id=client_id)
    return {"message": "Perfil de cliente eliminado exitosamente."}

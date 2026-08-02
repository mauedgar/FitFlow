"""
Endpoints para Membership (asíncrono, Sprint 5)
-----------------------------------------------
• CRUD completo para membresías.
• Validación de cliente antes de crear.
• Filtros avanzados: plan, estado, cliente.
• Requiere permisos de administrador.
"""

from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app import crud, schemas
from app.models import Membership, User, UserRole

router = APIRouter(prefix="/memberships", tags=["memberships"])


# ------------------------------------------------------------------ #
# Crear Membership
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.Membership, status_code=status.HTTP_201_CREATED)
async def create_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_in: schemas.MembershipCreate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    client = await crud.client.get(db, id=membership_in.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    membership = await crud.membership.create(db=db, obj_in=membership_in)
    return membership


# ------------------------------------------------------------------ #
# Listar Memberships con filtros
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Membership])
async def read_memberships(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[UUID] = None,
    status: Optional[str] = None,
    plan: Optional[str] = None,
    current_user: User = Depends(crud.user.get_current_admin),
):
    memberships = await crud.membership.get_multi_filtered(
        db=db,
        client_id=client_id,
        status=status,
        plan=plan,
        skip=skip,
        limit=limit,
    )
    return memberships


# ------------------------------------------------------------------ #
# Obtener Membership por ID
# ------------------------------------------------------------------ #
@router.get("/{membership_id}", response_model=schemas.Membership)
async def read_membership_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    current_user: User = Depends(crud.user.get_current_admin),
):
    membership = await crud.membership.get(db, id=membership_id, include_relations=True)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    return membership


# ------------------------------------------------------------------ #
# Actualizar Membership
# ------------------------------------------------------------------ #
@router.put("/{membership_id}", response_model=schemas.Membership)
async def update_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    membership_in: schemas.MembershipUpdate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    membership = await crud.membership.get(db, id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    updated = await crud.membership.update(db, db_obj=membership, obj_in=membership_in)
    return updated


# ------------------------------------------------------------------ #
# Eliminar Membership
# ------------------------------------------------------------------ #
@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    current_user: User = Depends(crud.user.get_current_admin),
):
    membership = await crud.membership.get(db, id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    await crud.membership.remove(db, id=membership_id)
    return {"message": "Membresía eliminada exitosamente."}

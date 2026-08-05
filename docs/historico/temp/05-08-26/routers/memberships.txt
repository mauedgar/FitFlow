"""
Router Membership (Sprint 6–7)
------------------------------
• CRUD de membresías.
• Endpoints públicos y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""
# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID

from app import crud, schemas
from app.db.session import get_async_session
from app.models.user import User
from app.services.membership_service import (
    to_membership_public,
    to_membership_with_client,
    to_membership_with_stats,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.deps import require_admin

router = APIRouter(prefix="/memberships", tags=["memberships"])


# --------------------------------------------------------------------------- #
# Crear Membership
# --------------------------------------------------------------------------- #
@router.post("/", response_model=schemas.MembershipPublic, status_code=status.HTTP_201_CREATED)
async def create_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_in: schemas.MembershipCreate,
    current_user: User = Depends(require_admin),
):
    """Crea una membresía para un cliente."""
    client = await crud.client.get(db, id=membership_in.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado.")

    membership = await crud.membership.create(db=db, obj_in=membership_in)
    return to_membership_public(membership)


# --------------------------------------------------------------------------- #
# Listar Memberships (admin)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[schemas.MembershipPublic])
async def read_memberships(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    client_id: UUID | None = None,
    status: str | None = None,
    plan: str | None = None,
    current_user: User = Depends(require_admin),
):
    """Lista membresías en versión pública."""
    memberships = await crud.membership.get_multi_filtered(
        db=db,
        client_id=client_id,
        status=status,
        plan=plan,
        skip=skip,
        limit=limit,
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Obtener Membership por ID (admin)
# --------------------------------------------------------------------------- #
@router.get("/{membership_id}", response_model=schemas.MembershipWithClient)
async def read_membership_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    current_user: User = Depends(require_admin),
):
    """Obtiene una membresía con datos del cliente."""
    membership = await crud.membership.get(db, id=membership_id, include_relations=True)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    return to_membership_with_client(membership)


# --------------------------------------------------------------------------- #
# Actualizar Membership
# --------------------------------------------------------------------------- #
@router.put("/{membership_id}", response_model=schemas.MembershipPublic)
async def update_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    membership_in: schemas.MembershipUpdate,
    current_user: User = Depends(require_admin),
):
    """Actualiza una membresía."""
    membership = await crud.membership.get(db, id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    updated = await crud.membership.update(db, db_obj=membership, obj_in=membership_in)
    return to_membership_public(updated)


# --------------------------------------------------------------------------- #
# Eliminar Membership
# --------------------------------------------------------------------------- #
@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_membership(
    *,
    db: AsyncSession = Depends(get_async_session),
    membership_id: UUID,
    current_user: User = Depends(require_admin),
):
    """Elimina una membresía."""
    membership = await crud.membership.get(db, id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    await crud.membership.remove(db, id=membership_id)
    return {"message": "Membresía eliminada exitosamente."}


# --------------------------------------------------------------------------- #
# Memberships públicas por cliente
# --------------------------------------------------------------------------- #
@router.get("/client/{client_id}/public", response_model=list[schemas.MembershipPublic])
async def read_memberships_by_client_public(
    *,
    client_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista membresías públicas de un cliente."""
    memberships = await crud.membership.get_multi_filtered(
        db=db,
        client_id=client_id,
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Memberships activas
# --------------------------------------------------------------------------- #
@router.get("/active", response_model=list[schemas.MembershipPublic])
async def read_active_memberships(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin),
):
    """Lista membresías activas."""
    memberships = await crud.membership.get_multi_filtered(
        db=db,
        status="active",
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Estadísticas de membresías
# --------------------------------------------------------------------------- #
@router.get("/stats", response_model=list[schemas.MembershipWithStats])
async def read_membership_stats(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin),
):
    """Devuelve estadísticas básicas de todas las membresías."""
    memberships = await crud.membership.get_multi(db)
    return [to_membership_with_stats(m) for m in memberships]

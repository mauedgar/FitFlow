"""Router Membership (Sprint 6-7).

-----------------------------------------
• CRUD de membresías de clientes.
• Endpoints públicos y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
• Compatible con TanStack Query.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import require_admin
from app.core.enums import MembershipStatus
from app.crud.crud_client import client
from app.crud.crud_membership import membership
from app.db.session import get_async_session
from app.services.membership_service import (
    to_membership_public,
    to_membership_with_client,
    to_membership_with_stats,
)
from app.schemas.membership import (
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    MembershipWithClient,
    MembershipWithStats,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

# ruff: noqa: ARG001
router = APIRouter(prefix="/memberships", tags=["memberships"])


# --------------------------------------------------------------------------- #
# Crear Membership
# --------------------------------------------------------------------------- #
@router.post("/", response_model=MembershipPublic, status_code=status.HTTP_201_CREATED)
async def create_membership(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    membership_in: MembershipCreate,
    current_user: Annotated[User, Depends(require_admin)],
) -> MembershipPublic:
    """Crea una membresía para un cliente.

    Reglas:
        • Solo administradores pueden crear membresías.
        • El cliente debe existir.
    """
    clientt = await client.get(db=db, obj_id=membership_in.client_id)
    if not clientt:
        raise HTTPException(404, "Cliente no encontrado.")

    membershipp = await membership.create(db=db, obj_in=membership_in)
    return to_membership_public(membershipp)


# --------------------------------------------------------------------------- #
# Listar Memberships (admin)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[MembershipPublic])
async def read_memberships(  # noqa: PLR0913
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 100,
    client_id: UUID | None = None,
    status: str | None = None,
    plan: str | None = None,
    current_user: Annotated[User, Depends(require_admin)],
) -> list[MembershipPublic]:
    """Lista membresías en versión pública (admin).

    Filtros disponibles:
        • client_id
        • status
        • plan
        • paginación (skip/limit)
    """
    memberships = await membership.get_multi_filtered(
        db=db,
        client_id=client_id,
        status=status, # pyright: ignore[reportArgumentType]
        plan=plan, # pyright: ignore[reportArgumentType]
        skip=skip,
        limit=limit,
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Obtener Membership por ID (admin)
# --------------------------------------------------------------------------- #
@router.get("/{membership_id}", response_model=MembershipWithClient)
async def read_membership_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    membership_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
) -> MembershipWithClient:
    """Obtiene una membresía con datos del cliente.

    Incluye:
        • Datos públicos de la membresía.
        • Datos públicos del cliente asociado.
    """
    membershipp = await membership.get(
        db=db,
        obj_id=membership_id,
        include_relations=True,
    )
    if not membershipp:
        raise HTTPException(404, "Membresía no encontrada.")

    return to_membership_with_client(membershipp)


# --------------------------------------------------------------------------- #
# Actualizar Membership
# --------------------------------------------------------------------------- #
@router.put("/{membership_id}", response_model=MembershipPublic)
async def update_membership(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    membership_id: UUID,
    membership_in: MembershipUpdate,
    current_user: Annotated[User, Depends(require_admin)],
) -> MembershipPublic:
    """Actualiza una membresía.

    Permite modificar:
        • plan
        • estado
        • fechas
        • último check-in
        • último invoice
    """
    membershipp = await membership.get(db=db, obj_id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    updated = await membership.update(db=db, db_obj=membershipp, obj_in=membership_in) # pyright: ignore[reportArgumentType]
    return to_membership_public(updated)


# --------------------------------------------------------------------------- #
# Eliminar Membership
# --------------------------------------------------------------------------- #
@router.delete("/{membership_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_membership(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    membership_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
) -> dict[str, str]:
    """Elimina una membresía (soft delete)."""
    membershipp = await membership.get(db=db, obj_id=membership_id)
    if not membership:
        raise HTTPException(404, "Membresía no encontrada.")

    await membership.remove(db=db, db_obj=membershipp) # pyright: ignore[reportArgumentType]
    return {"message": "Membresía eliminada exitosamente."}


# --------------------------------------------------------------------------- #
# Memberships públicas por cliente
# --------------------------------------------------------------------------- #
@router.get("/client/{client_id}/public", response_model=list[MembershipPublic])
async def read_memberships_by_client_public(
    *,
    client_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[MembershipPublic]:
    """Lista membresías públicas de un cliente."""
    memberships = await membership.get_multi_filtered(
        db=db,
        client_id=client_id,
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Memberships activas
# --------------------------------------------------------------------------- #
@router.get("/active", response_model=list[MembershipPublic])
async def read_active_memberships(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[MembershipPublic]:
    """Lista membresías activas."""
    memberships = await membership.get_multi_filtered(
        db=db,
        status=MembershipStatus.active,
    )
    return [to_membership_public(m) for m in memberships]


# --------------------------------------------------------------------------- #
# Estadísticas de membresías
# --------------------------------------------------------------------------- #
@router.get("/stats", response_model=list[MembershipWithStats])
async def read_membership_stats(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> list[MembershipWithStats]:
    """Devuelve estadísticas básicas de todas las membresías.

    Incluye:
        • total de reservas
        • reservas futuras
    """
    memberships = await membership.get_multi(db=db)
    return [to_membership_with_stats(m) for m in memberships]

"""Router Membership (Sprint 6-7).

-----------------------------------------
• CRUD de membresías de clientes.
• Endpoints públicos y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
• Compatible con TanStack Query.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_current_user
from app.core.enums import MembershipStatus
from app.crud.crud_client import client
from app.crud.crud_membership import membership
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.membership import (
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    MembershipWithClient,
    MembershipWithStats,
)
from app.schemas.user import UserPublic
from app.services.errors import PermissionDeniedError
from app.services.membership_service import (
    to_membership_public,
    to_membership_with_client,
    to_membership_with_stats,
)

# ruff: noqa: ARG001
router = APIRouter(prefix="/memberships", tags=["memberships"])


async def _require_membership_admin(
    user: Annotated[UserPublic, Depends(require_current_user)],
) -> UserPublic:
    """Map the existing admin role guard to the selected Membership HTTP boundary."""
    try:
        return await require_admin(user)
    except PermissionDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


MembershipAdminUser = Annotated[UserPublic, Depends(_require_membership_admin)]


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
# Memberships activas
# --------------------------------------------------------------------------- #
@router.get("/active", response_model=list[MembershipPublic])
async def read_active_memberships(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: MembershipAdminUser,
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
    current_user: MembershipAdminUser,
) -> list[MembershipWithStats]:
    """Devuelve estadísticas básicas de todas las membresías.

    Incluye:
        • total de reservas
        • reservas futuras
    """
    memberships = await membership.get_multi(db=db)
    return [to_membership_with_stats(m) for m in memberships]

# --------------------------------------------------------------------------- #
# Obtener Membership por ID (admin)
# --------------------------------------------------------------------------- #
@router.get("/{membership_id}", response_model=MembershipWithClient)
async def read_membership_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    membership_id: UUID,
    current_user: MembershipAdminUser,
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
    if not membershipp:
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
    if not membershipp:
        raise HTTPException(404, "Membresía no encontrada.")

    cancelled = await membership.update(
        db=db,
        db_obj=membershipp,
        obj_in=MembershipUpdate(status=MembershipStatus.cancelled, end_date=datetime.now(UTC)),
    )
    return {"message": f"Membresía {cancelled.id} cancelada exitosamente."}


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

"""
CRUD para Membership (asíncrono, Sprint 6–7)
--------------------------------------------
• CRUD completo para membresías de clientes.
• Filtros avanzados: por cliente, por estado, por plan.
• Compatible con SQLAlchemy 2.0 async.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import MembershipPlan, MembershipStatus
from app.models import Membership
from app.schemas.membership import MembershipCreate, MembershipUpdate

from .base import CRUDBase


class CRUDMembership(CRUDBase[Membership, MembershipCreate, MembershipUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> Membership | None:
        """
        Obtiene una membresía por su ID, con opción de incluir relaciones.
        """
        opts = (
            [selectinload(Membership.client)]
            if include_relations
            else None
        )
        return await super().get(db, id=id, options=opts)

    # ------------------------------------------------------------------ #
    # Filtros avanzados
    # ------------------------------------------------------------------ #
    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *,
        client_id: UUID | None = None,
        status: MembershipStatus | None = None,
        plan: MembershipPlan | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """
        Obtiene una lista filtrada de membresías.
        Permite filtrar por cliente, estado y plan.
        """
        stmt = (
            select(Membership)
            .where(Membership.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )

        if client_id:
            stmt = stmt.where(Membership.client_id == client_id)

        if status:
            stmt = stmt.where(Membership.status == status)

        if plan:
            stmt = stmt.where(Membership.plan == plan)

        stmt = stmt.options(selectinload(Membership.client))

        res = await db.execute(stmt)
        return res.scalars().unique().all()


membership = CRUDMembership(Membership)

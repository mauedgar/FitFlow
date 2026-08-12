"""CRUD para Membership (asíncrono, Sprint 6-7).

--------------------------------------------
• CRUD completo para membresías de clientes.
• Filtros avanzados: por cliente, por estado, por plan.
• Compatible con SQLAlchemy 2.0 async.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from backend.app.db.models import Membership
from app.schemas.membership import MembershipCreate, MembershipUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

    from app.core.enums import MembershipPlan, MembershipStatus


class CRUDMembership(CRUDBase[Membership, MembershipCreate, MembershipUpdate]):
    """CRUD especializado para membresías de clientes."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_relations: bool = False,
    ) -> Membership | None:
        """Obtiene una membresía por ID, con opción de incluir relaciones."""
        opts: list[ORMOption] | None = (
            [selectinload(Membership.client)]
            if include_relations
            else None
        )
        return await super().get(db, obj_id=obj_id, options=opts)

    # ------------------------------------------------------------------ #
    # Filtros avanzados
    # ------------------------------------------------------------------ #
    async def get_multi_filtered(  # noqa: PLR0913
        self,
        db: AsyncSession,
        *,
        client_id: UUID | None = None,
        status: MembershipStatus | None = None,
        plan: MembershipPlan | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Membership]:
        """Obtiene una lista filtrada de membresías según criterios avanzados."""
        stmt = (
            select(Membership)
            .where(Membership.deleted_at.is_(None))  # type: ignore[attr-defined]
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
        return list(res.scalars().unique().all())


membership = CRUDMembership(Membership)

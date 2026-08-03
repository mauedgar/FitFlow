"""
CRUD para ClassSession (asíncrono, Sprint 6–7)
----------------------------------------------
• Representa una ocurrencia concreta de un ClassSchedule.
• Filtros avanzados: rango de fechas, estado, disponibilidad.
• Incluye método get_or_create asíncrono.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ClassSchedule, ClassSession
from app.schemas.class_session import ClassSessionCreate, ClassSessionUpdate

from ..core.enums import ClassSessionStatus
from .base import CRUDBase


class CRUDClassSession(CRUDBase[ClassSession, ClassSessionCreate, ClassSessionUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> ClassSession | None:
        """
        Obtiene una sesión concreta por su ID, con opción de incluir relaciones.
        """
        opts = (
            [
                selectinload(ClassSession.class_schedule),
                selectinload(ClassSession.bookings),
            ]
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
        schedule_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: ClassSessionStatus | None = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ClassSession]:
        """
        Obtiene una lista filtrada de sesiones.
        Permite filtrar por horario, rango de fechas, estado y disponibilidad.
        """
        stmt = (
            select(ClassSession)
            .where(ClassSession.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )

        if schedule_id:
            stmt = stmt.where(ClassSession.class_schedule_id == schedule_id)

        if date_from:
            stmt = stmt.where(
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time())
            )

        if date_to:
            stmt = stmt.where(
                ClassSession.starts_at <= datetime.combine(date_to, datetime.max.time())
            )

        if status:
            stmt = stmt.where(ClassSession.status == status)

        if available_only:
            stmt = stmt.join(ClassSession.class_schedule).where(
                ClassSession.capacity_snapshot < ClassSchedule.capacity
            )

        stmt = stmt.options(
            selectinload(ClassSession.class_schedule),
            selectinload(ClassSession.bookings),
        )

        res = await db.execute(stmt)
        return res.scalars().unique().all()

    # ------------------------------------------------------------------ #
    # get_or_create (versión asíncrona)
    # ------------------------------------------------------------------ #
    async def get_or_create(
        self,
        db: AsyncSession,
        *,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[ClassSession, bool]:
        """
        Busca una sesión por criterios (kwargs).
        Si existe → la devuelve.
        Si no existe → la crea con kwargs + defaults.
        """
        stmt = select(ClassSession).filter_by(**kwargs)
        res = await db.execute(stmt)
        instance = res.scalars().first()

        if instance:
            return instance, False

        create_data = {**kwargs, **(defaults or {})}
        instance = ClassSession(**create_data)

        db.add(instance)
        await db.flush()  # asigna ID sin commit

        return instance, True


# Instancia reusable
class_session = CRUDClassSession(ClassSession)

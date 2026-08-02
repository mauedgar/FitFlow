"""
CRUD para ClassSession (asíncrono, Sprint 5)
--------------------------------------------
• Representa una ocurrencia concreta de un ClassSchedule.
• Filtros avanzados: rango de fechas, disponibilidad, estado.
• Incluye método get_or_create asíncrono.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, List
from uuid import UUID
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ClassSession
from app.schemas.class_session import ClassSessionCreate, ClassSessionUpdate
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
    ) -> Optional[ClassSession]:
        opts = (
            [
                selectinload(ClassSession.schedule),
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
        schedule_id: Optional[UUID] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ClassSession]:
        stmt = (
            select(ClassSession)
            .where(ClassSession.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )

        if schedule_id:
            stmt = stmt.where(ClassSession.schedule_id == schedule_id)

        if date_from:
            stmt = stmt.where(ClassSession.start_datetime >= datetime.combine(date_from, datetime.min.time()))

        if date_to:
            stmt = stmt.where(ClassSession.start_datetime <= datetime.combine(date_to, datetime.max.time()))

        stmt = stmt.options(
            selectinload(ClassSession.schedule),
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
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple[ClassSession, bool]:
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


class_session = CRUDClassSession(ClassSession)

"""
CRUD para ClassSchedule (asíncrono, Sprint 5)
---------------------------------------------
• Representa la configuración recurrente de una clase dentro de la agenda del gimnasio.
• Filtros avanzados: gym_class_id, teacher_id, allowed_plan, día de la semana, rango de fechas, activo.
• Incluye carga selectiva de relaciones (gym_class, teacher, sessions).
"""

from __future__ import annotations
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ClassSchedule
from app.schemas.class_schedule import ClassScheduleCreate, ClassScheduleUpdate
from .base import CRUDBase


class CRUDClassSchedule(CRUDBase[ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> Optional[ClassSchedule]:
        """
        Obtiene un horario recurrente por su ID, con opción de incluir relaciones.
        """
        opts = (
            [
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.sessions),
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
        skip: int = 0,
        limit: int = 100,
        gym_class_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        allowed_plan: Optional[str] = None,
        day_of_week: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        active: Optional[bool] = True,
        search: Optional[str] = None,
    ) -> List[ClassSchedule]:
        """
        Obtiene una lista filtrada de horarios recurrentes de clases.
        Permite filtrar por clase, profesor, plan permitido, día, rango de fechas y estado.
        """
        stmt = select(ClassSchedule).where(ClassSchedule.deleted_at.is_(None))

        if active is not None:
            stmt = stmt.where(ClassSchedule.active.is_(active))

        if gym_class_id:
            stmt = stmt.where(ClassSchedule.gym_class_id == gym_class_id)

        if teacher_id:
            stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)

        if allowed_plan:
            stmt = stmt.where(ClassSchedule.allowed_plan == allowed_plan)

        if day_of_week is not None:
            stmt = stmt.where(ClassSchedule.days_of_week.contains([day_of_week]))

        if date_from:
            stmt = stmt.where(ClassSchedule.start_date >= date_from)

        if date_to:
            stmt = stmt.where(
                (ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date <= date_to)
            )

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(ClassSchedule.gym_class.has(func.lower(ClassSchedule.gym_class.name).ilike(like)))
            )

        stmt = (
            stmt.options(
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.sessions),
            )
            .order_by(ClassSchedule.start_time)
            .offset(skip)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().unique().all()


# Instancia reusable
class_schedule = CRUDClassSchedule(ClassSchedule)

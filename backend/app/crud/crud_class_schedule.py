"""
CRUD para ClassSchedule (asíncrono, Sprint 6–7)
-----------------------------------------------
• Representa la configuración recurrente de una clase dentro de la agenda.
• Filtros avanzados: clase, profesor, allowed_plan, día, rango de fechas, activo.
• Carga selectiva de relaciones (gym_class, teacher, class_sessions).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ClassSchedule, GymClass
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
    ) -> ClassSchedule | None:
        """
        Obtiene un horario recurrente por su ID, con opción de incluir relaciones.
        """
        opts = (
            [
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.class_sessions),
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
        gym_class_id: UUID | None = None,
        teacher_id: UUID | None = None,
        allowed_plan: str | None = None,
        day_of_week: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        active: bool | None = True,
        search: str | None = None,
    ) -> list[ClassSchedule]:
        """
        Obtiene una lista filtrada de horarios recurrentes de clases.
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
            stmt = stmt.join(ClassSchedule.gym_class).where(
                func.lower(GymClass.name).ilike(like)
            )

        stmt = (
            stmt.options(
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.class_sessions),
            )
            .order_by(ClassSchedule.start_time)
            .offset(skip)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().unique().all()


# Instancia reusable
class_schedule = CRUDClassSchedule(ClassSchedule)

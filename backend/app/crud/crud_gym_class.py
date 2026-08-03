"""
CRUD para GymClass (asíncrono, Sprint 5)
----------------------------------------
• Sin relación directa con Teacher (usa ClassSchedule).
• Filtros avanzados: difficulty, activity_type, search, teacher, día, rango fechas.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ClassSchedule, GymClass
from app.schemas.gym_class import GymClassCreate, GymClassUpdate

from .base import CRUDBase


class CRUDGymClass(CRUDBase[GymClass, GymClassCreate, GymClassUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_schedules: bool = False,
    ) -> None | GymClass:
        opts = [selectinload(GymClass.class_schedules)] if include_schedules else None
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
        difficulty: None | str = None,
        activity_type: None | str = None,
        active: None | bool = True,
        search: None | str = None,
        teacher_id: None | UUID = None,
        day_of_week: None | int = None,
        date_from: None | date = None,
        date_to: None | date = None,
    ) -> list[GymClass]:
        stmt = select(GymClass).where(GymClass.deleted_at.is_(None))

        if active is not None:
            stmt = stmt.where(GymClass.active.is_(active))

        if difficulty:
            stmt = stmt.where(GymClass.difficulty == difficulty)

        if activity_type:
            stmt = stmt.where(GymClass.activity_type == activity_type)

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(GymClass.name).ilike(like) | func.lower(GymClass.description).ilike(like)
            )

        # Filtros que implican JOIN con ClassSchedule
        if teacher_id or day_of_week is not None or date_from or date_to:
            stmt = stmt.join(ClassSchedule)

            if teacher_id:
                stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)

            if day_of_week is not None:
                stmt = stmt.where(ClassSchedule.days_of_week.contains([day_of_week]))

            if date_from:
                stmt = stmt.where(ClassSchedule.start_date >= date_from)

            if date_to:
                stmt = stmt.where(
                    (ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date <= date_to)
                )

        stmt = (
            stmt.options(selectinload(GymClass.class_schedules))
            .order_by(GymClass.name)
            .offset(skip)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return res.scalars().unique().all()


# Instancia reusable
gym_class = CRUDGymClass(GymClass)
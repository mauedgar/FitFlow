"""CRUD para GymClass (asíncrono, Sprint 5).

----------------------------------------
• Sin relación directa con Teacher (usa ClassSchedule).
• Filtros avanzados: difficulty, activity_type, search, teacher, día, rango fechas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from backend.app.db.models import ClassSchedule, GymClass
from app.schemas.gym_class import GymClassCreate, GymClassUpdate

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption


class CRUDGymClass(CRUDBase[GymClass, GymClassCreate, GymClassUpdate]):
    """CRUD especializado para clases del gimnasio."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_schedules: bool = False,
    ) -> GymClass | None:
        """Obtiene una clase del gimnasio según criterios avanzados."""
        opts: list[ORMOption] | None = (
            [selectinload(GymClass.class_schedules)]
            if include_schedules
            else None
        )
        return await super().get(db, obj_id=obj_id, options=opts)

    # ------------------------------------------------------------------ #
    # Filtros avanzados
    # ------------------------------------------------------------------ #
    async def get_multi_filtered(    # noqa: PLR0913 — muchos argumentos son necesarios para filtros avanzados
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        difficulty: str | None = None,
        activity_type: str | None = None,
        active: bool | None = True,
        search: str | None = None,
        teacher_id: UUID | None = None,
        day_of_week: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[GymClass]:
        """Obtiene una lista filtrada de clases del gimnasio según criterios avanzados."""
        stmt = select(GymClass).where(
            GymClass.deleted_at.is_(None),  # type: ignore[attr-defined]
        )

        if active is not None:
            stmt = stmt.where(GymClass.active.is_(active))  # type: ignore[attr-defined]

        if difficulty:
            stmt = stmt.where(GymClass.difficulty == difficulty)

        if activity_type:
            stmt = stmt.where(GymClass.activity_type == activity_type)

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(GymClass.name).ilike(like)
                | func.lower(GymClass.description).ilike(like),
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
                    (ClassSchedule.end_date.is_(None))  # type: ignore[attr-defined]
                    | (ClassSchedule.end_date <= date_to),  # type: ignore[attr-defined]
                )

        stmt = (
            stmt.options(selectinload(GymClass.class_schedules))
            .order_by(GymClass.name)
            .offset(skip)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return list(res.scalars().unique().all())


# Instancia reusable
gym_class = CRUDGymClass(GymClass)

# app/crud/crud_class_schedule.py
"""CRUD para ClassSchedule (asíncrono, Sprint 6-7).

• Representa la configuración recurrente de una clase dentro de la agenda.
• Filtros avanzados: clase, profesor, allowed_plan, día, rango de fechas, activo.
• Carga selectiva de relaciones (gym_class, teacher, class_sessions).
• Validaciones simples en create/update; reglas complejas en services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import ClassSchedule, GymClass
from app.schemas.class_schedule import ClassScheduleCreate, ClassScheduleUpdate
from app.services import errors as svc_errors

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption
# ruff: noqa: UP037

class CRUDClassSchedule(CRUDBase[ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate]):
    """CRUD especializado para horarios recurrentes de clases."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: "AsyncSession",
        *,
        obj_id: "UUID",
        include_relations: bool = False,
    ) -> ClassSchedule | None:
        """Obtiene un horario recurrente por su ID.

        Si include_relations=True carga gym_class, teacher y class_sessions.
        """
        opts: list["ORMOption"] | None = (
            [
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.class_sessions),
            ]
            if include_relations
            else None
        )
        return await super().get(db, obj_id=obj_id, options=opts)

    # ------------------------------------------------------------------ #
    # Filtros avanzados
    # ------------------------------------------------------------------ #
    async def get_multi_filtered(  # noqa: C901, PLR0913
        self,
        db: "AsyncSession",
        *,
        skip: int = 0,
        limit: int = 100,
        gym_class_id: "UUID | None" = None,
        teacher_id: "UUID | None" = None,
        allowed_plan: str | None = None,
        day_of_week: int | None = None,
        date_from: "date | None" = None,
        date_to: "date | None" = None,
        active: bool | None = True,
        search: str | None = None,
        include_relations: bool = False,
    ) -> list[ClassSchedule]:
        """Obtiene una lista filtrada de horarios recurrentes.

        Nota: la evaluación de availability (por capacity_snapshot/current_bookings_count)
        debe hacerse en el service; aquí se exponen filtros relacionales y de ventana.
        """
        stmt = select(ClassSchedule).where(
            ClassSchedule.deleted_at.is_(None),  # type: ignore[attr-defined]
        )

        if active is not None:
            stmt = stmt.where(ClassSchedule.active.is_(active))  # type: ignore[attr-defined]

        if gym_class_id:
            stmt = stmt.where(ClassSchedule.gym_class_id == gym_class_id)

        if teacher_id:
            stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)

        if allowed_plan:
            stmt = stmt.where(ClassSchedule.allowed_plan == allowed_plan)

        if day_of_week is not None:
            # days_of_week assumed to be an array/JSON field containing ints 0..6
            stmt = stmt.where(ClassSchedule.days_of_week.contains([day_of_week]))

        if date_from and date_to:
            # schedules that overlap the [date_from, date_to] window
            stmt = stmt.where(
                ClassSchedule.start_date <= date_to,
                (ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date >= date_from),  # type: ignore[attr-defined]
            )
        elif date_from:
            stmt = stmt.where(
                (ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date >= date_from),  # type: ignore[attr-defined]
            )
        elif date_to:
            stmt = stmt.where(ClassSchedule.start_date <= date_to)

        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.join(ClassSchedule.gym_class).where(
                func.lower(GymClass.name).ilike(like),
            )

        if include_relations:
            stmt = stmt.options(
                selectinload(ClassSchedule.gym_class),
                selectinload(ClassSchedule.teacher),
                selectinload(ClassSchedule.class_sessions),
            )

        stmt = (
            stmt.order_by(ClassSchedule.start_time)
            .offset(skip)
            .limit(limit)
        )

        res = await db.execute(stmt)
        return list(res.scalars().unique().all())

    # ------------------------------------------------------------------ #
    # Create / Update / Remove (CRUDBase proporciona create/update/remove básicos)
    # ------------------------------------------------------------------ #
    async def create(
        self,
        db: "AsyncSession",
        *,
        obj_in: ClassScheduleCreate,
        created_by: object | None = None,  # noqa: ARG002
    ) -> ClassSchedule:
        """Crea un ClassSchedule.

        No genera ClassSession aquí; la generación automática debe orquestarse desde el service.
        Lanza BusinessValidationError en caso de violaciones simples (ej. capacity < 0).
        """
        data = obj_in.model_dump()
        capacity = data.get("capacity")
        if capacity is not None and int(capacity) < 0:
            msg = "Capacity debe ser >= 0."
            raise svc_errors.BusinessValidationError(msg)
        db_obj = ClassSchedule(**data)  # type: ignore[arg-type]
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: "AsyncSession",
        *,
        db_obj: ClassSchedule,
        obj_in: ClassScheduleUpdate,
    ) -> ClassSchedule:
        """Actualiza un ClassSchedule.

        No genera ni borra ClassSession automáticamente; el service decide la generación/actualización de sesiones.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        if "capacity" in update_data and int(update_data["capacity"]) < 0:
            msg = "Capacity debe ser >= 0."
            raise svc_errors.BusinessValidationError(msg)
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def remove(
        self,
        db: "AsyncSession",
        *,
        obj_id: "UUID",
    ) -> None:
        """Elimina (o marca como borrado) un ClassSchedule.

        Validar integridad con ClassSession/Bookings en el service si es necesario.
        """
        obj = await self.get(db, obj_id=obj_id)
        if not obj:
            msg = "ClassSchedule no encontrado."
            raise svc_errors.NotFoundError(msg)
        await super().remove(db, db_obj=obj)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    async def get_active_schedules_for_class(
        self,
        db: "AsyncSession",
        *,
        gym_class_id: "UUID",
        date_from: "date | None" = None,
        date_to: "date | None" = None,
    ) -> list[ClassSchedule]:
        """Devuelve schedules activos para una clase en un rango opcional.

        Útil para el service que genera ClassSession a partir del schedule.
        """
        stmt = select(ClassSchedule).where(
            ClassSchedule.gym_class_id == gym_class_id,
            ClassSchedule.active.is_(True),  # type: ignore[attr-defined]
            ClassSchedule.deleted_at.is_(None),  # type: ignore[attr-defined]
        )

        if date_from and date_to:
            stmt = stmt.where(
                ClassSchedule.start_date <= date_to,
                (ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date >= date_from),  # type: ignore[attr-defined]
            )
        elif date_from:
            stmt = stmt.where((ClassSchedule.end_date.is_(None)) | (ClassSchedule.end_date >= date_from))  # type: ignore[attr-defined]
        elif date_to:
            stmt = stmt.where(ClassSchedule.start_date <= date_to)

        res = await db.execute(stmt)
        return list(res.scalars().all())


# Instancia reusable
class_schedule = CRUDClassSchedule(ClassSchedule)

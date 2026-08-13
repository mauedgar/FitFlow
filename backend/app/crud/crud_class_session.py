"""CRUD para ClassSession (asíncrono, Sprint 6-7).

----------------------------------------------
• Representa una ocurrencia concreta de un ClassSchedule.
• Filtros avanzados: rango de fechas, estado, disponibilidad.
• Incluye método get_or_create asíncrono.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.db.models import ClassSchedule, ClassSession
from app.schemas.class_session import ClassSessionCreate, ClassSessionUpdate
from app.services import errors as svc_errors

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

    from app.core.enums import ClassSessionStatus


class CRUDClassSession(CRUDBase[ClassSession, ClassSessionCreate, ClassSessionUpdate]):
    """CRUD especializado para sesiones de clase."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_relations: bool = False,
    ) -> ClassSession | None:
        """Obtiene una sesión concreta por su ID, con opción de incluir relaciones."""
        opts: list[ORMOption] | None = (
            [
                selectinload(ClassSession.class_schedule),
                selectinload(ClassSession.bookings),
            ]
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
        schedule_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: ClassSessionStatus | None = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 100,
        teacher_id: UUID | None = None,
        include_relations: bool = False,
        gym_class_id: UUID | None = None,
    ) -> list[ClassSession]:
        """Obtiene una lista filtrada de sesiones."""
        stmt = (
            select(ClassSession)
            .where(ClassSession.active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        if gym_class_id:
            stmt = stmt.join(ClassSession.class_schedule).where(
                ClassSchedule.gym_class_id == gym_class_id,
            )
        if teacher_id:
            stmt = stmt.join(ClassSession.class_schedule).where(
                ClassSchedule.teacher_id == teacher_id,
        )
        if schedule_id:
            stmt = stmt.where(ClassSession.class_schedule_id == schedule_id)

        if date_from:
            stmt = stmt.where(
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time()),
            )

        if date_to:
            stmt = stmt.where(
                ClassSession.starts_at <= datetime.combine(date_to, datetime.max.time()),
            )

        if status:
            stmt = stmt.where(ClassSession.status == status)

        if available_only:
            stmt = stmt.join(ClassSession.class_schedule).where(
                ClassSession.capacity_snapshot < ClassSchedule.capacity,
            )

        # 🔥 SOLO si se pide include_relations
        if include_relations:
            stmt = stmt.options(
                selectinload(ClassSession.class_schedule)
                    .selectinload(ClassSchedule.gym_class),
                selectinload(ClassSession.class_schedule)
                    .selectinload(ClassSchedule.teacher),
                selectinload(ClassSession.bookings),
            )

        res = await db.execute(stmt)
        return list(res.scalars().unique().all())


    # ------------------------------------------------------------------ #
    # get_or_create (versión asíncrona)
    # ------------------------------------------------------------------ #
    async def get_or_create(
        self,
        db: AsyncSession,
        *,
        defaults: dict[str, object] | None = None,
        **kwargs: object,
    ) -> tuple[ClassSession, bool]:
        """Busca una sesión por criterios (kwargs). Si existe, la devuelve; si no, la crea."""
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

    async def create_with_capacity_snapshot(
        self,
        db: "AsyncSession",  # noqa: UP037
        *,
        obj_in: ClassSessionCreate,
        created_by: object | None = None,  # noqa: ARG002
    ) -> ClassSession:
        """Crea una ClassSession y persiste el capacity_snapshot tal como viene en el schema."""
        data = obj_in.model_dump()
        db_obj = ClassSession(**data)  # type: ignore[arg-type]
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError as err:
            await db.rollback()
            msg = "No se pudo crear la sesión."
            raise svc_errors.BusinessValidationError(msg) from err
        await db.refresh(db_obj)
        return db_obj


# Instancia reusable
class_session = CRUDClassSession(ClassSession)

"""CRUD para Booking (asíncrono, Sprint 6-7).

-----------------------------------------
• Representa la reserva de una ClassSession por parte de un cliente.
• Filtros avanzados: por cliente, sesión, estado, fechas, check-in.
• Carga selectiva de relaciones (client, class_session, schedule, gym_class).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Booking, ClassSchedule, ClassSession
from app.schemas.booking import BookingCreate, BookingUpdate

from .base import CRUDBase

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

    from app.core.enums import BookingStatus


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD especializado para reservas (Booking)."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_relations: bool = False,
    ) -> Booking | None:
        """Obtiene una reserva por ID, con opción de incluir relaciones profundas."""
        opts: list[ORMOption] | None = (
            [
                selectinload(Booking.client),
                selectinload(Booking.class_session)
                .selectinload(ClassSession.class_schedule)
                .selectinload(ClassSchedule.gym_class),
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
        client_id: UUID | None = None,
        session_id: UUID | None = None,
        status: BookingStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        checked_in: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        """Aplica filtros avanzados para obtener reservas según distintos criterios."""
        stmt = (
            select(Booking)
            .where(Booking.deleted_at.is_(None))  # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )

        if client_id:
            stmt = stmt.where(Booking.client_id == client_id)
        if session_id:
            stmt = stmt.where(Booking.class_session_id == session_id)
        if status:
            stmt = stmt.where(Booking.status == status)
        if date_from:
            stmt = stmt.join(Booking.class_session).where(
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time()),
            )
        if date_to:
            stmt = stmt.join(Booking.class_session).where(
                ClassSession.starts_at <= datetime.combine(date_to, datetime.max.time()),
            )
        if checked_in is True:
            stmt = stmt.where(Booking.checked_in_at.is_not(None))
        elif checked_in is False:
            stmt = stmt.where(Booking.checked_in_at.is_(None))

        stmt = stmt.options(
            selectinload(Booking.client),
            selectinload(Booking.class_session)
            .selectinload(ClassSession.class_schedule)
            .selectinload(ClassSchedule.gym_class),
        )

        res = await db.execute(stmt)
        return list(res.scalars().unique().all())

    # ------------------------------------------------------------------ #
    # Búsqueda específica: evitar duplicados
    # ------------------------------------------------------------------ #
    async def get_by_client_and_session(
        self,
        db: AsyncSession,
        *,
        client_id: UUID,
        session_id: UUID,
    ) -> Booking | None:
        """Devuelve una reserva si el cliente ya reservó esa sesión (para evitar duplicados)."""
        stmt = (
            select(Booking)
            .where(
                Booking.client_id == client_id,
                Booking.class_session_id == session_id,
                Booking.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    # ------------------------------------------------------------------ #
    # Búsqueda con relaciones profundas
    # ------------------------------------------------------------------ #
    async def get_with_relations(
        self,
        db: AsyncSession,
        *,
        booking_id: UUID,
    ) -> Booking | None:
        """Devuelve una reserva con todas sus relaciones cargadas."""
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id, Booking.deleted_at.is_(None))  # type: ignore[attr-defined]
            .options(
                selectinload(Booking.client),
                selectinload(Booking.class_session)
                .selectinload(ClassSession.class_schedule)
                .selectinload(ClassSchedule.gym_class),
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()


booking = CRUDBooking(Booking)

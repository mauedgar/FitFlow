"""
CRUD para Booking (asíncrono, Sprint 6–7)
-----------------------------------------
• Representa la reserva de una ClassSession por parte de un cliente.
• Filtros avanzados: por cliente, sesión, estado, fechas, check-in.
• Carga selectiva de relaciones (client, class_session, schedule, gym_class).
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Booking, ClassSchedule, ClassSession
from app.schemas.booking import BookingCreate, BookingUpdate

from ..core.enums import BookingStatus
from .base import CRUDBase


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> Booking | None:
        """
        Obtiene una reserva por ID, con opción de incluir relaciones profundas.
        """
        opts = (
            [
                selectinload(Booking.client),
                selectinload(Booking.class_session)
                    .selectinload(ClassSession.class_schedule)
                    .selectinload(ClassSchedule.gym_class),
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
        client_id: UUID | None = None,
        session_id: UUID | None = None,
        status: BookingStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        checked_in: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        """
        Filtros avanzados para reservas:
            • por cliente
            • por sesión
            • por estado
            • por rango de fechas (starts_at)
            • por check-in
        """
        stmt = (
            select(Booking)
            .where(Booking.deleted_at.is_(None))
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
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time())
            )

        if date_to:
            stmt = stmt.join(Booking.class_session).where(
                ClassSession.starts_at <= datetime.combine(date_to, datetime.max.time())
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
        return res.scalars().unique().all()

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
        """
        Devuelve una reserva si el cliente ya reservó esa sesión.
        Útil para evitar duplicados antes de crear una reserva.
        """
        stmt = (
            select(Booking)
            .where(
                Booking.client_id == client_id,
                Booking.class_session_id == session_id,
                Booking.deleted_at.is_(None),
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
        """
        Devuelve una reserva con todas sus relaciones cargadas:
            • client
            • class_session
            • class_schedule
            • gym_class
        """
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id, Booking.deleted_at.is_(None))
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

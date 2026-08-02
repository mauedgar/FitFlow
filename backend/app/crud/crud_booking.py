"""
CRUD para Booking (asíncrono, Sprint 5)
---------------------------------------
• Representa la reserva de una ClassSession por parte de un cliente.
• Filtros avanzados: por usuario, por sesión, por estado.
• La lógica de negocio (capacidad, duplicados, estado) se maneja en el endpoint.
"""

from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Booking
from app.schemas.booking import BookingCreate, BookingUpdate
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
    ) -> Optional[Booking]:
        opts = (
            [
                selectinload(Booking.client),
                selectinload(Booking.class_session),
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
        client_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Booking]:
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

        stmt = stmt.options(
            selectinload(Booking.client),
            selectinload(Booking.class_session),
        )

        res = await db.execute(stmt)
        return res.scalars().unique().all()


booking = CRUDBooking(Booking)

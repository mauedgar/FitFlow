"""CRUD para Booking (asíncrono, Sprint 6-7).

• Representa la reserva de una ClassSession por parte de un cliente.
• Filtros avanzados: por cliente, sesión, estado, fechas, check-in.
• Carga selectiva de relaciones (client, class_session, schedule, gym_class).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import Booking, ClassSchedule, ClassSession
from app.schemas.booking import BookingCreate, BookingCreateInternal, BookingUpdate

# Excepciones de dominio centralizadas
from app.services.errors import ConflictError, NotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

    from app.core.enums import BookingStatus

# ruff: noqa: UP037
class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD especializado para reservas (Booking)."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: "AsyncSession",
        *,
        obj_id: "UUID",
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
        db: "AsyncSession",
        *,
        client_id: "UUID | None" = None,
        session_id: "UUID | None" = None,
        status: "BookingStatus | None" = None,
        date_from: "date | None" = None,
        date_to: "date | None" = None,
        checked_in: "bool | None" = None,
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

        # Unir class_session solo si hace falta (evitar joins duplicados)
        joined_session = False
        if date_from or date_to:
            stmt = stmt.join(Booking.class_session)
            joined_session = True  # noqa: F841

        if date_from:
            stmt = stmt.where(
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time()),
            )
        if date_to:
            stmt = stmt.where(
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
        db: "AsyncSession",
        *,
        client_id: "UUID",
        session_id: "UUID",
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
        db: "AsyncSession",
        *,
        booking_id: "UUID",
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

    # ------------------------------------------------------------------ #
    # Creación atómica con verificación de capacidad
    # ------------------------------------------------------------------ #
    async def create_with_capacity_check(
        self,
        db: "AsyncSession",
        *,
        client_id: "UUID",
        session_id: "UUID",
        obj_in: "BookingCreateInternal",  # o BookingCreateInternal según tu flujo
    ) -> Booking:
        """Crea una reserva de forma atómica verificando capacidad y duplicados.

        Parámetros
        ----------
        db: AsyncSession
            Sesión de base de datos (transaccional).
        client_id: UUID
            ID del cliente que reserva.
        session_id: UUID
            ID de la ClassSession a reservar.
        obj_in: BookingCreate
            Esquema de creación.

        Retorna
        -------
        Booking
            Instancia ORM creada.

        Lanza
        -----
        NotFoundError
            Si la ClassSession no existe.
        ConflictError
            Si no hay cupo o ya existe reserva duplicada.
        """
        async with db.begin():  # abre transacción
            q = select(ClassSession).where(ClassSession.id == session_id).with_for_update()
            res = await db.execute(q)
            session = res.scalar_one_or_none()
            if session is None:
                msg = "ClassSession no encontrada."
                raise NotFoundError(msg)

            # asegurar tipos concretos para linters
            capacity = int(session.capacity_snapshot) # pyright: ignore[reportArgumentType]
            current = int(session.current_bookings_count)
            available = capacity - current
            if available <= 0:
                msg_0 = "No hay lugares disponibles para esta sesión."
                raise ConflictError(msg_0)

            # verificar duplicado
            q2 = select(Booking).where(
                Booking.class_session_id == session_id,
                Booking.client_id == client_id,
                Booking.cancelled_at.is_(None),  # si usás soft delete
            )
            res2 = await db.execute(q2)
            if res2.scalar_one_or_none():
                msg_1 = "Ya tienes una reserva para esta sesión."
                raise ConflictError(msg_1)

            # crear booking (adaptá si obj_in es otro tipo)
            booking = Booking(**obj_in.dict())
            db.add(booking)

            # actualizar contador en la sesión (si lo mantenés en la tabla)
            session.current_bookings_count = current + 1
            await db.flush()  # asegura INSERT/UPDATE en la transacción

            return booking


booking = CRUDBooking(Booking)

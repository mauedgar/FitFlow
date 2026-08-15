"""CRUD para Booking (asíncrono, Sprint 6-7).

• Representa la reserva de una ClassSession por parte de un cliente.
• Filtros avanzados: por cliente, sesión, estado, fechas, check-in.
• Carga selectiva de relaciones (client, class_session, schedule, gym_class).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.enums import BookingStatus, ClassSessionStatus
from app.crud.base import CRUDBase
from app.db.models import Booking, ClassSchedule, ClassSession
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
        schedule_id: "UUID | None" = None,
        gym_class_id: "UUID | None" = None,
        status: "BookingStatus | None" = None,
        date: "date | None" = None,
        date_from: "date | None" = None,
        date_to: "date | None" = None,
        checked_in: "bool | None" = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        """Aplica filtros avanzados para obtener reservas según distintos criterios."""
        stmt = select(Booking).offset(skip).limit(limit)

        if client_id:
            stmt = stmt.where(Booking.client_id == client_id)
        if session_id:
            stmt = stmt.where(Booking.class_session_id == session_id)
        if status:
            stmt = stmt.where(Booking.status == status)

        # Join only when a session or schedule attribute is filtered.
        if date_from or date_to or date or schedule_id or gym_class_id:
            stmt = stmt.join(Booking.class_session)
        if schedule_id or gym_class_id:
            stmt = stmt.join(ClassSession.class_schedule)
        if schedule_id:
            stmt = stmt.where(ClassSchedule.id == schedule_id)
        if gym_class_id:
            stmt = stmt.where(ClassSchedule.gym_class_id == gym_class_id)

        if date_from:
            stmt = stmt.where(
                ClassSession.starts_at >= datetime.combine(date_from, datetime.min.time()),
            )
        if date_to:
            stmt = stmt.where(
                ClassSession.starts_at <= datetime.combine(date_to, datetime.max.time()),
            )
        if date:
            stmt = stmt.where(
                ClassSession.starts_at >= datetime.combine(date, datetime.min.time()),
                ClassSession.starts_at <= datetime.combine(date, datetime.max.time()),
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
                Booking.status != BookingStatus.cancelled,
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
            .where(Booking.id == booking_id)
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
            if (
                not session.active
                or session.deleted_at is not None
                or session.status not in {ClassSessionStatus.scheduled, ClassSessionStatus.open}
            ):
                raise ConflictError("La sesión no admite reservas.")

            capacity = int(session.capacity_snapshot) # pyright: ignore[reportArgumentType]
            count_stmt = select(func.count(Booking.id)).where(
                Booking.class_session_id == session_id,
                Booking.status != BookingStatus.cancelled,
            )
            current = int((await db.scalar(count_stmt)) or 0)
            available = capacity - current
            if available <= 0:
                msg_0 = "No hay lugares disponibles para esta sesión."
                raise ConflictError(msg_0)

            # verificar duplicado
            q2 = select(Booking).where(
                Booking.class_session_id == session_id,
                Booking.client_id == client_id,
                Booking.status != BookingStatus.cancelled,
            )
            res2 = await db.execute(q2)
            if res2.scalar_one_or_none():
                msg_1 = "Ya tienes una reserva para esta sesión."
                raise ConflictError(msg_1)

            # crear booking (adaptá si obj_in es otro tipo)
            booking = Booking(**obj_in.model_dump())
            db.add(booking)
            await db.flush()  # asegura INSERT/UPDATE en la transacción

            return booking


booking = CRUDBooking(Booking)

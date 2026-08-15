"""Business operations and typed views for the Front Desk module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from app.core.enums import BookingStatus, ClassSessionStatus
from app.core.timezone import LOCAL_TZ
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_gym_class import gym_class
from app.db.models import Booking, ClassSchedule, ClassSession, Client
from app.schemas.front_desk import (
    FrontDeskBookingView,
    FrontDeskClassView,
    FrontDeskDayView,
    FrontDeskSessionView,
    SessionCapacity,
)
from app.services.errors import BusinessValidationError, ConflictError, NotFoundError


def _session_options() -> list[ORMOption]:
    """Load every relationship required by Front Desk views explicitly."""
    return [
        selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.gym_class),
        selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.teacher),
        selectinload(ClassSession.bookings).selectinload(Booking.client).selectinload(Client.user),
    ]


async def _get_session(db: AsyncSession, session_id: UUID) -> ClassSession:
    stmt = (
        select(ClassSession)
        .where(
            ClassSession.id == session_id,
            ClassSession.active.is_(True),
            ClassSession.deleted_at.is_(None),
        )
        .options(*_session_options())
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None:
        msg = "ClassSession no encontrada."
        raise NotFoundError(msg)
    return session


async def get_sessions_today(
    db: AsyncSession,
    *,
    teacher_id: UUID | None = None,
    gym_class_id: UUID | None = None,
) -> FrontDeskDayView:
    """Return today's operational sessions in the configured local timezone."""
    today = datetime.now(LOCAL_TZ).date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=LOCAL_TZ).astimezone(UTC)
    end = datetime.combine(today, datetime.max.time(), tzinfo=LOCAL_TZ).astimezone(UTC)
    stmt = (
        select(ClassSession)
        .join(ClassSession.class_schedule)
        .where(
            ClassSession.starts_at >= start,
            ClassSession.starts_at <= end,
            ClassSession.active.is_(True),
            ClassSession.deleted_at.is_(None),
        )
        .options(*_session_options())
        .order_by(ClassSession.starts_at)
    )
    if teacher_id is not None:
        stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)
    if gym_class_id is not None:
        stmt = stmt.where(ClassSchedule.gym_class_id == gym_class_id)

    sessions = (await db.execute(stmt)).scalars().unique().all()
    return FrontDeskDayView(date=today, sessions=[to_frontdesk_session_view(item) for item in sessions])


async def get_session_bookings(db: AsyncSession, session_id: UUID) -> list[FrontDeskBookingView]:
    """Return operational booking views for one session."""
    session = await _get_session(db, session_id)
    return [to_frontdesk_booking_view(booking) for booking in session.bookings]


async def get_session_capacity(db: AsyncSession, session_id: UUID) -> SessionCapacity:
    """Return derived capacity without mutating a hybrid property."""
    session = await _get_session(db, session_id)
    return SessionCapacity(
        session_id=session.id,
        capacity=session.capacity_snapshot,
        used=session.current_bookings_count,
        available=session.available_spots,
    )


async def cancel_session(db: AsyncSession, session_id: UUID) -> FrontDeskSessionView:
    """Cancel an operational session while preserving its bookings."""
    session = await _get_session(db, session_id)
    if session.status == ClassSessionStatus.cancelled:
        msg = "La sesión ya fue cancelada."
        raise ConflictError(msg)
    if session.status == ClassSessionStatus.completed:
        msg_0 = "Una sesión completada no puede cancelarse."
        raise BusinessValidationError(msg_0)
    session.status = ClassSessionStatus.cancelled
    await db.commit()
    return to_frontdesk_session_view(await _get_session(db, session_id))


async def check_in_booking(
    db: AsyncSession,
    *,
    session_id: UUID,
    booking_id: UUID,
) -> FrontDeskBookingView:
    """Record a single check-in through the confirmed-to-attended transition."""
    stmt = (
        select(Booking)
        .where(Booking.id == booking_id, Booking.class_session_id == session_id)
        .options(
            selectinload(Booking.client).selectinload(Client.user),
            selectinload(Booking.class_session),
        )
        .with_for_update()
    )
    booking = (await db.execute(stmt)).scalar_one_or_none()
    if booking is None:
        msg = "Reserva no encontrada para la sesión indicada."
        raise NotFoundError(msg)
    if booking.status != BookingStatus.confirmed:
        msg_0 = "Solo una reserva confirmada puede registrar check-in."
        raise ConflictError(msg_0)
    if booking.class_session.status not in {ClassSessionStatus.scheduled, ClassSessionStatus.open}:
        msg_1 = "La sesión no admite check-in."
        raise BusinessValidationError(msg_1)

    booking.status = BookingStatus.attended
    booking.checked_in_at = datetime.now(UTC)
    await db.commit()
    refreshed = (
        await db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.client).selectinload(Client.user)),
        )
    ).scalar_one()
    return to_frontdesk_booking_view(refreshed)


async def get_active_classes(db: AsyncSession) -> list[FrontDeskClassView]:
    """Return active catalog items using the Front Desk contract."""
    classes = await gym_class.get_multi_filtered(db=db, active=True)
    return [
        FrontDeskClassView(
            id=item.id,
            name=item.name,
            difficulty=item.difficulty,
            activity_type=item.activity_type,
        )
        for item in classes
    ]


async def get_schedule_by_class(db: AsyncSession, class_id: UUID) -> list[ClassSchedule]:
    """Return active schedules; their public projection belongs to the router contract."""
    return await class_schedule.get_multi_filtered(
        db=db,
        gym_class_id=class_id,
        include_relations=True,
    )


def to_frontdesk_booking_view(booking: Booking) -> FrontDeskBookingView:
    """Build a compact operational booking projection."""
    return FrontDeskBookingView(
        id=booking.id,
        client_id=booking.client_id,
        client_name=f"{booking.client.first_name} {booking.client.last_name}",
        client_email=booking.client.user.email,
        status=booking.status,
    )


def to_frontdesk_session_view(session: ClassSession) -> FrontDeskSessionView:
    """Build a compact operational session projection from loaded relations."""
    schedule = session.class_schedule
    gym_class = schedule.gym_class
    teacher = schedule.teacher
    now = datetime.now(UTC)
    return FrontDeskSessionView(
        id=session.id,
        class_schedule_id=schedule.id,
        gym_class_id=gym_class.id,
        teacher_id=teacher.id,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
        gym_class_name=gym_class.name,
        teacher_full_name=teacher.full_name,
        capacity_snapshot=session.capacity_snapshot,
        current_bookings_count=session.current_bookings_count,
        available_spots=session.available_spots,
        is_live=session.starts_at <= now <= session.ends_at,
        is_upcoming=session.starts_at > now,
        is_full=session.available_spots == 0,
        is_empty=session.current_bookings_count == 0,
    )

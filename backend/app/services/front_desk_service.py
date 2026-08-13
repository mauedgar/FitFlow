"""Servicios del módulo Front Desk.

Orquesta:
• sesiones del día
• capacidad
• reservas
• clases activas
• horarios por clase
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_class_session import class_session
from app.crud.crud_gym_class import gym_class
from app.db.models import ClassSchedule, ClassSession
from app.schemas.front_desk import (
    FrontDeskBookingView,
    FrontDeskDayView,
    FrontDeskSessionView,
    SessionCapacity,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

# --------------------------------------------------------------------------- #
# SESIONES DEL DÍA
# --------------------------------------------------------------------------- #

async def get_sessions_today(db: AsyncSession) -> FrontDeskDayView:
    """Devuelve todas las sesiones del día actual en formato FrontDesk."""
    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    today = datetime.now(tz).date()

    start_dt = datetime.combine(today, datetime.min.time(), tzinfo=tz)
    end_dt = datetime.combine(today, datetime.max.time(), tzinfo=tz)

    stmt = (
        select(ClassSession)
        .where(ClassSession.starts_at >= start_dt)
        .where(ClassSession.starts_at <= end_dt)
        .options(
            selectinload(ClassSession.class_schedule)
            .selectinload(ClassSchedule.gym_class),
            selectinload(ClassSession.class_schedule)
            .selectinload(ClassSchedule.teacher),
            selectinload(ClassSession.bookings)
            .selectinload("client") # pyright: ignore[reportArgumentType]
            .selectinload("client.user"), # pyright: ignore[reportArgumentType]
        )
        .order_by(ClassSession.starts_at)
    )

    res = await db.execute(stmt)
    sessions = res.scalars().unique().all()

    views = [to_frontdesk_session_view(s) for s in sessions]

    return FrontDeskDayView(date=today, sessions=views)


# --------------------------------------------------------------------------- #
# CAPACIDAD DISPONIBLE
# --------------------------------------------------------------------------- #

async def get_session_capacity(db: AsyncSession, session_id: UUID) -> SessionCapacity | None:
    """Devuelve la capacidad disponible de una sesión."""
    session = await class_session.get(db, obj_id=session_id, include_relations=True)
    if not session:
        return None

    return SessionCapacity(
        session_id=session.id, # pyright: ignore[reportArgumentType]
        capacity=session.capacity_snapshot, # pyright: ignore[reportArgumentType]
        used=session.current_bookings_count,
        available=session.available_spots,
    )


# --------------------------------------------------------------------------- #
# CANCELAR SESIÓN
# --------------------------------------------------------------------------- #

async def cancel_session(db: AsyncSession, session_id: UUID) -> ClassSession | None:
    """Cancela una sesión (status = cancelled)."""
    session = await class_session.get(db, obj_id=session_id)
    if not session:
        return None

    return await class_session.update(
        db=db,
        db_obj=session,
        obj_in={"status": "cancelled"},
    )


# --------------------------------------------------------------------------- #
# RESERVAS DE UNA SESIÓN
# --------------------------------------------------------------------------- #

async def get_session_bookings(db: AsyncSession, session_id: UUID) -> list[FrontDeskBookingView] | None:
    """Devuelve todas las reservas de una sesión en formato FrontDesk."""
    session = await class_session.get(db, obj_id=session_id, include_relations=True)
    if not session:
        return None

    return [
        FrontDeskBookingView(
            id=b.id, # pyright: ignore[reportArgumentType]
            client_id=b.client_id, # pyright: ignore[reportArgumentType]
            client_name=b.client.full_name, # pyright: ignore[reportAttributeAccessIssue]
            client_email=b.client.user.email, # pyright: ignore[reportArgumentType]
            status=b.status, # pyright: ignore[reportArgumentType]
        )
        for b in session.bookings
    ]


# --------------------------------------------------------------------------- #
# CLASES ACTIVAS
# --------------------------------------------------------------------------- #

async def get_active_classes(db: AsyncSession) -> list:
    """Devuelve todas las clases activas."""
    return await gym_class.get_multi_filtered(db=db, active=True)


# --------------------------------------------------------------------------- #
# AGENDA SEMANAL POR CLASE
# --------------------------------------------------------------------------- #

async def get_schedule_by_class(db: AsyncSession, class_id: UUID) -> list[ClassSchedule]:
    """Devuelve los horarios semanales de una clase."""
    return await class_schedule.get_multi_filtered(db=db, gym_class_id=class_id)


# --------------------------------------------------------------------------- #
# CONSTRUCTOR DE VISTA
# --------------------------------------------------------------------------- #

def to_frontdesk_session_view(session: ClassSession) -> FrontDeskSessionView:
    """Construye la vista operativa de una sesión."""
    schedule = session.class_schedule
    gym_class = schedule.gym_class
    teacher = schedule.teacher

    return FrontDeskSessionView(
        id=session.id, # pyright: ignore[reportArgumentType]
        class_schedule_id=schedule.id, # pyright: ignore[reportArgumentType]
        gym_class_id=gym_class.id, # pyright: ignore[reportArgumentType]
        teacher_id=teacher.id, # pyright: ignore[reportArgumentType]

        starts_at=session.starts_at, # pyright: ignore[reportArgumentType]
        ends_at=session.ends_at, # pyright: ignore[reportArgumentType]
        status=session.status, # pyright: ignore[reportArgumentType]

        gym_class_name=gym_class.name, # pyright: ignore[reportArgumentType]
        teacher_full_name=teacher.full_name,

        capacity_snapshot=session.capacity_snapshot, # pyright: ignore[reportArgumentType]
        current_bookings_count=session.current_bookings_count,
        available_spots=session.available_spots,

        is_live=session.starts_at <= datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")) <= session.ends_at, # pyright: ignore[reportArgumentType]
        is_upcoming=session.starts_at > datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")), # pyright: ignore[reportArgumentType]
        is_full=session.available_spots == 0,
        is_empty=session.current_bookings_count == 0,
    )

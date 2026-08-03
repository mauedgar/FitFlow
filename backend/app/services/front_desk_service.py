# app/services/front_desk_service.py

"""
Servicios del módulo Front Desk
--------------------------------
• Lógica operativa del gimnasio (sesiones del día, reservas, capacidad, etc.)
• No expone endpoints.
• Reutilizable desde routers y otros módulos.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import crud
from app.models import ClassSchedule, ClassSession


# --------------------------------------------------------------------------- #
# SESIONES DEL DÍA
# --------------------------------------------------------------------------- #
async def get_sessions_today(db: AsyncSession):
    """
    Devuelve todas las sesiones del día actual con sus relaciones cargadas.
    """
    today = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())

    stmt = (
        select(ClassSession)
        .where(ClassSession.start_datetime >= start_dt)
        .where(ClassSession.start_datetime <= end_dt)
        .options(
            selectinload(ClassSession.schedule)
            .selectinload(ClassSchedule.gym_class),
            selectinload(ClassSession.bookings),
        )
        .order_by(ClassSession.start_datetime)
    )

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# --------------------------------------------------------------------------- #
# CAPACIDAD DISPONIBLE
# --------------------------------------------------------------------------- #
async def get_session_capacity(db: AsyncSession, session_id: UUID):
    """
    Calcula la capacidad disponible de una sesión.
    """
    session = await crud.class_session.get(db, id=session_id, include_relations=True)
    if not session:
        return None

    used = len(session.bookings)
    available = session.capacity_snapshot - used

    return {
        "session": session,
        "used": used,
        "available": available,
    }


# --------------------------------------------------------------------------- #
# CANCELAR SESIÓN
# --------------------------------------------------------------------------- #
async def cancel_session(db: AsyncSession, session_id: UUID):
    """
    Cancela una sesión (status = 'cancelled').
    """
    session = await crud.class_session.get(db, id=session_id)
    if not session:
        return None

    updated = await crud.class_session.update(
        db=db,
        db_obj=session,
        obj_in={"status": "cancelled"},
    )
    return updated


# --------------------------------------------------------------------------- #
# RESERVAS DE UNA SESIÓN
# --------------------------------------------------------------------------- #
async def get_session_bookings(db: AsyncSession, session_id: UUID):
    """
    Devuelve todas las reservas de una sesión.
    """
    session = await crud.class_session.get(db, id=session_id, include_relations=True)
    if not session:
        return None

    return session.bookings


# --------------------------------------------------------------------------- #
# CLASES ACTIVAS
# --------------------------------------------------------------------------- #
async def get_active_classes(db: AsyncSession):
    """
    Devuelve todas las clases activas.
    """
    return await crud.gym_class.get_multi_filtered(db=db, active=True)


# --------------------------------------------------------------------------- #
# AGENDA SEMANAL POR CLASE
# --------------------------------------------------------------------------- #
async def get_schedule_by_class(db: AsyncSession, class_id: UUID):
    """
    Devuelve los horarios semanales de una clase.
    """
    return await crud.class_schedule.get_multi_filtered(db=db, gym_class_id=class_id)

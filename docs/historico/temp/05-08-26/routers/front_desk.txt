"""
Router Front Desk (asíncrono, Sprint 6–7)
-----------------------------------------
• Endpoints operativos para el rol front_desk.
• Usa services para lógica de negocio.
• Devuelve schemas públicos y operativos.
• Optimizado para TanStack Query.
"""
# ruff: noqa: B008

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app import crud, schemas
from app.db.session import get_async_session
from app.models.class_schedule import ClassSchedule
from app.models.class_session import ClassSession
from app.models.user import User
from app.services.booking_service import to_booking_public
from app.services.class_schedule_service import to_class_schedule_public
from app.services.class_session_service import (
    to_class_session_response,
    update_session_availability,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.deps import require_admin_or_front_desk

router = APIRouter(prefix="/front-desk", tags=["front-desk"])


# --------------------------------------------------------------------------- #
# SESIONES DEL DÍA
# --------------------------------------------------------------------------- #
@router.get("/sessions/today", response_model=list[schemas.ClassSessionInResponse])
async def get_sessions_today(
    *,
    teacher_id: UUID | None = None,
    class_id: UUID | None = None,
    include_bookings: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Devuelve todas las sesiones del día actual.
    Vista operativa para mesa de entrada.
    """
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
            .selectinload(ClassSchedule.gym_class)
        )
        .order_by(ClassSession.starts_at)
    )

    # Filtros operativos
    if teacher_id:
        stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)

    if class_id:
        stmt = stmt.where(ClassSchedule.gym_class_id == class_id)

    # Cargar reservas si se solicita
    if include_bookings:
        stmt = stmt.options(selectinload(ClassSession.bookings))

    res = await db.execute(stmt)
    sessions = res.scalars().unique().all()

    # Transformación automática + disponibilidad
    return [
        to_class_session_response(update_session_availability(s))
        for s in sessions
    ]


# --------------------------------------------------------------------------- #
# RESERVAS DE UNA SESIÓN
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/bookings", response_model=list[schemas.BookingPublic])
async def get_session_bookings(
    *,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Devuelve todas las reservas de una sesión (versión pública).
    """
    session = await crud.class_session.get(db, id=session_id, include_relations=True)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    return [to_booking_public(b) for b in session.bookings]


# --------------------------------------------------------------------------- #
# CAPACIDAD DISPONIBLE
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/capacity", response_model=schemas.SessionCapacity)
async def get_session_capacity(
    *,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Devuelve la capacidad disponible de una sesión.
    """
    session = await crud.class_session.get(db, id=session_id, include_relations=True)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    session = update_session_availability(session)

    return schemas.SessionCapacity(
        session_id=session.id,
        capacity=session.class_schedule.capacity,
        used=session.current_bookings_count,
        available=session.available_spots,
    )


# --------------------------------------------------------------------------- #
# CANCELAR SESIÓN
# --------------------------------------------------------------------------- #
@router.post("/sessions/{session_id}/cancel", response_model=schemas.ClassSessionInResponse)
async def cancel_session(
    *,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Cancela una sesión (no la elimina).
    Cambia el estado a 'cancelled'.
    """
    session = await crud.class_session.get(db, id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    updated = await crud.class_session.update(
        db=db,
        db_obj=session,
        obj_in=schemas.ClassSessionUpdate(status="cancelled"),
    )

    updated = update_session_availability(updated)
    return to_class_session_response(updated)


# --------------------------------------------------------------------------- #
# CLASES ACTIVAS (público-operativo)
# --------------------------------------------------------------------------- #
@router.get("/classes", response_model=list[schemas.GymClassPublic])
async def get_active_classes(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Devuelve todas las clases activas (versión pública).
    """
    classes = await crud.gym_class.get_multi_filtered(db=db, active=True)
    return [schemas.GymClassPublic.model_validate(c) for c in classes]


# --------------------------------------------------------------------------- #
# AGENDA SEMANAL POR CLASE (público-operativo)
# --------------------------------------------------------------------------- #
@router.get("/schedule", response_model=list[schemas.ClassSchedulePublic])
async def get_schedule_by_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_front_desk),
):
    """
    Devuelve los horarios semanales de una clase (versión pública).
    """
    schedules = await crud.class_schedule.get_multi_filtered(db=db, gym_class_id=class_id)

    return [to_class_schedule_public(s) for s in schedules]

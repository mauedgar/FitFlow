"""Router Front Desk (asíncrono, Sprint 6-7).

-----------------------------------------
• Endpoints operativos para el rol front_desk.
• Usa services y CRUD para lógica de negocio.
• Devuelve públicos y operativos.
• Optimizado para TanStack Query.
• Sin SQLAlchemy directo.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import require_admin_or_front_desk
from app.core.enums import ClassSessionStatus
from app.core.timezone import LOCAL_TZ
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_class_session import class_session
from app.crud.crud_gym_class import gym_class
from app.db.session import get_async_session
from app.services.booking_service import to_booking_public
from app.services.class_schedule_service import to_class_schedule_public
from app.services.class_session_service import (
    to_class_session_response,
    update_session_availability,
)
from app.schemas.booking import BookingPublic
from app.schemas.class_schedule import ClassSchedulePublic
from app.schemas.class_session import ClassSessionInResponse, ClassSessionUpdate
from app.schemas.front_desk import SessionCapacity
from app.schemas.gym_class import GymClassPublic

# ruff: noqa: ARG001
if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User


router = APIRouter(prefix="/front-desk", tags=["front-desk"])


# --------------------------------------------------------------------------- #
# SESIONES DEL DÍA
# --------------------------------------------------------------------------- #
@router.get("/sessions/today", response_model=list[ClassSessionInResponse])
async def get_sessions_today(
    *,
    teacher_id: UUID | None = None,
    gym_class_id: UUID | None = None,
    include_bookings: bool = False,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> list[ClassSessionInResponse]:
    """Devuelve todas las sesiones del día actual.

    Vista operativa para mesa de entrada.
    """
    today: date = datetime.now(LOCAL_TZ).date()

    sessions = await class_session.get_multi_filtered(
        db=db,
        date_from=today,
        date_to=today,
        teacher_id=teacher_id,
        gym_class_id=gym_class_id,
        include_relations=include_bookings,
    )

    return [
        to_class_session_response(update_session_availability(s))
        for s in sessions
    ]


# --------------------------------------------------------------------------- #
# RESERVAS DE UNA SESIÓN
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/bookings", response_model=list[BookingPublic])
async def get_session_bookings(
    *,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas de una sesión (versión pública)."""
    session = await class_session.get(
        db=db,
        obj_id=session_id,
        include_relations=True,
    )

    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    return [to_booking_public(b) for b in session.bookings]


# --------------------------------------------------------------------------- #
# CAPACIDAD DISPONIBLE
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/capacity", response_model=SessionCapacity)
async def get_session_capacity(
    *,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> SessionCapacity:
    """Devuelve la capacidad disponible de una sesión."""
    session = await class_session.get(
        db=db,
        obj_id=session_id,
        include_relations=True,
    )

    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    session = update_session_availability(session)

    return SessionCapacity(
        session_id=session.id, # pyright: ignore[reportArgumentType]
        capacity=session.class_schedule.capacity, # pyright: ignore[reportArgumentType]
        used=session.current_bookings_count,
        available=session.available_spots,
    )


# --------------------------------------------------------------------------- #
# CANCELAR SESIÓN
# --------------------------------------------------------------------------- #
@router.post("/sessions/{session_id}/cancel", response_model=ClassSessionInResponse)
async def cancel_session(
    *,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> ClassSessionInResponse:
    """Cancela una sesión (no la elimina).

    Cambia el estado a 'cancelled'.
    """
    session = await class_session.get(db=db, obj_id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    updated = await class_session.update(
        db=db,
        db_obj=session,
        obj_in=ClassSessionUpdate(status=ClassSessionStatus.cancelled),
    )

    updated = update_session_availability(updated)
    return to_class_session_response(updated)


# --------------------------------------------------------------------------- #
# CLASES ACTIVAS (público-operativo)
# --------------------------------------------------------------------------- #
@router.get("/classes", response_model=list[GymClassPublic])
async def get_active_classes(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> list[GymClassPublic]:
    """Devuelve todas las clases activas (versión pública)."""
    classes = await gym_class.get_multi_filtered(db=db, active=True)
    return [GymClassPublic.model_validate(c) for c in classes]


# --------------------------------------------------------------------------- #
# AGENDA SEMANAL POR CLASE (público-operativo)
# --------------------------------------------------------------------------- #
@router.get("/schedule", response_model=list[ClassSchedulePublic])
async def get_schedule_by_class(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(require_admin_or_front_desk)],
) -> list[ClassSchedulePublic]:
    """Devuelve los horarios semanales de una clase (versión pública)."""
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        gym_class_id=class_id,
    )

    return [to_class_schedule_public(s) for s in schedules]

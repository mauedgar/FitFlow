"""HTTP boundary for Front Desk operations."""

from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin_or_front_desk
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.class_schedule import ClassSchedulePublic
from app.schemas.front_desk import (
    FrontDeskBookingView,
    FrontDeskClassView,
    FrontDeskDayView,
    FrontDeskSessionView,
    SessionCapacity,
)
from app.services import front_desk_service
from app.services.class_schedule_service import to_class_schedule_public
from app.services.errors import BusinessValidationError, ConflictError, NotFoundError

router = APIRouter(prefix="/front-desk", tags=["front-desk"])
FrontDeskUser = Annotated[User, Depends(require_admin_or_front_desk)]
Database = Annotated[AsyncSession, Depends(get_async_session)]


def _raise_domain_error(exc: Exception) -> NoReturn:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    if isinstance(exc, BusinessValidationError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    raise exc


@router.get("/sessions/today", response_model=FrontDeskDayView)
async def get_sessions_today(
    db: Database,
    _: FrontDeskUser,
    teacher_id: UUID | None = None,
    gym_class_id: UUID | None = None,
) -> FrontDeskDayView:
    """Return today's operational board in the configured local timezone."""
    return await front_desk_service.get_sessions_today(
        db,
        teacher_id=teacher_id,
        gym_class_id=gym_class_id,
    )


@router.get("/sessions/{session_id}/bookings", response_model=list[FrontDeskBookingView])
async def get_session_bookings(session_id: UUID, db: Database, _: FrontDeskUser) -> list[FrontDeskBookingView]:
    try:
        return await front_desk_service.get_session_bookings(db, session_id)
    except (NotFoundError, ConflictError, BusinessValidationError) as exc:
        _raise_domain_error(exc)


@router.get("/sessions/{session_id}/capacity", response_model=SessionCapacity)
async def get_session_capacity(session_id: UUID, db: Database, _: FrontDeskUser) -> SessionCapacity:
    try:
        return await front_desk_service.get_session_capacity(db, session_id)
    except (NotFoundError, ConflictError, BusinessValidationError) as exc:
        _raise_domain_error(exc)


@router.post("/sessions/{session_id}/cancel", response_model=FrontDeskSessionView)
async def cancel_session(session_id: UUID, db: Database, _: FrontDeskUser) -> FrontDeskSessionView:
    try:
        return await front_desk_service.cancel_session(db, session_id)
    except (NotFoundError, ConflictError, BusinessValidationError) as exc:
        _raise_domain_error(exc)


@router.post(
    "/sessions/{session_id}/bookings/{booking_id}/check-in",
    response_model=FrontDeskBookingView,
)
async def check_in_booking(
    session_id: UUID,
    booking_id: UUID,
    db: Database,
    _: FrontDeskUser,
) -> FrontDeskBookingView:
    try:
        return await front_desk_service.check_in_booking(
            db,
            session_id=session_id,
            booking_id=booking_id,
        )
    except (NotFoundError, ConflictError, BusinessValidationError) as exc:
        _raise_domain_error(exc)


@router.get("/classes", response_model=list[FrontDeskClassView])
async def get_active_classes(db: Database, _: FrontDeskUser) -> list[FrontDeskClassView]:
    return await front_desk_service.get_active_classes(db)


@router.get("/schedule", response_model=list[ClassSchedulePublic])
async def get_schedule_by_class(class_id: UUID, db: Database, _: FrontDeskUser) -> list[ClassSchedulePublic]:
    schedules = await front_desk_service.get_schedule_by_class(db, class_id)
    return [to_class_schedule_public(item) for item in schedules]

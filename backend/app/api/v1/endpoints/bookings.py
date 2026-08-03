"""
Router Booking (Sprint 6–7)
---------------------------
• Reservas de sesiones.
• Endpoints públicos y privados.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""
# ruff: noqa: B008

from __future__ import annotations

from datetime import date
from uuid import UUID

from app import crud, schemas
from app.api.deps import (
    require_admin,
    require_admin_client_or_self,
    require_admin_or_client,
)
from app.db.session import get_async_session
from app.models.user import User
from app.services.booking_service import (
    to_booking_internal,
    to_booking_public,
    validate_booking_creation,
)
from app.services.class_session_service import update_session_availability
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/bookings", tags=["bookings"])


# --------------------------------------------------------------------------- #
# Crear Booking (cliente)
# --------------------------------------------------------------------------- #
@router.post("/", response_model=schemas.BookingPublic, status_code=status.HTTP_201_CREATED)
async def create_booking(
    *,
    db: AsyncSession = Depends(get_async_session),
    booking_in: schemas.BookingCreate,
    current_user: User = Depends(require_admin_or_client),
):
    session = await crud.class_session.get(
        db,
        id=booking_in.class_session_id,
        include_relations=True,
    )
    if not session:
        raise HTTPException(404, "La sesión no existe.")

    session = update_session_availability(session)
    validate_booking_creation(session)

    client_id = current_user.person_profile.client.id

    existing = await crud.booking.get_multi_filtered(
        db=db,
        client_id=client_id,
        session_id=session.id,
    )
    if existing:
        raise HTTPException(400, "Ya tienes una reserva para esta sesión.")

    booking_internal = to_booking_internal(
        client_id=client_id,
        session=session,
        status=schemas.BookingStatus.ACTIVE,
    )

    booking = await crud.booking.create(db=db, obj_in=booking_internal)
    return to_booking_public(booking)


# --------------------------------------------------------------------------- #
# Reservas del cliente actual
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=list[schemas.BookingPublic])
async def read_my_bookings(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_or_client),
):
    client_id = current_user.person_profile.client.id

    bookings = await crud.booking.get_multi_filtered(
        db=db,
        client_id=client_id,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Cancelar reserva
# --------------------------------------------------------------------------- #
@router.post("/{booking_id}/cancel", response_model=schemas.BookingPublic)
async def cancel_booking(
    *,
    booking_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin_client_or_self),
):
    booking = await crud.booking.get(db, id=booking_id, include_relations=True)
    if not booking:
        raise HTTPException(404, "Reserva no encontrada.")

    client_id = current_user.person_profile.client.id

    if current_user.role == "client" and booking.client_id != client_id:
        raise HTTPException(403, "No puedes cancelar reservas de otros clientes.")

    updated = await crud.booking.update(
        db=db,
        db_obj=booking,
        obj_in=schemas.BookingUpdate(status=schemas.BookingStatus.CANCELLED),
    )

    return to_booking_public(updated)


# --------------------------------------------------------------------------- #
# Verificar si se puede reservar una sesión
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/can-book", response_model=schemas.SessionCapacity)
async def can_book_session(
    *,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
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
# Reservas públicas por sesión
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/public", response_model=list[schemas.BookingPublic])
async def read_session_bookings_public(
    *,
    session_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    session = await crud.class_session.get(db, id=session_id, include_relations=True)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    return [to_booking_public(b) for b in session.bookings]


# --------------------------------------------------------------------------- #
# Reservas públicas por clase
# --------------------------------------------------------------------------- #
@router.get("/classes/{class_id}/public", response_model=list[schemas.BookingPublic])
async def read_class_bookings_public(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        class_id=class_id,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas públicas por horario
# --------------------------------------------------------------------------- #
@router.get("/class-schedules/{schedule_id}/public", response_model=list[schemas.BookingPublic])
async def read_schedule_bookings_public(
    *,
    schedule_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        schedule_id=schedule_id,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por día
# --------------------------------------------------------------------------- #
@router.get("/day", response_model=list[schemas.BookingPublic])
async def read_bookings_by_day(
    *,
    date_query: date,
    db: AsyncSession = Depends(get_async_session),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        date=date_query,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por rango
# --------------------------------------------------------------------------- #
@router.get("/range", response_model=list[schemas.BookingPublic])
async def read_bookings_by_range(
    *,
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_async_session),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        date_from=date_from,
        date_to=date_to,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por cliente (admin)
# --------------------------------------------------------------------------- #
@router.get("/client/{client_id}", response_model=list[schemas.BookingPublic])
async def read_bookings_by_client(
    *,
    client_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        client_id=client_id,
        include_relations=True,
    )
    return [to_booking_public(b) for b in bookings]

"""Router Booking (Sprint 6.5-7).

-----------------------------------------
• Gestión de reservas de sesiones.
• Endpoints públicos, privados y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import (
    require_admin,
    require_admin_client_or_self,
    require_admin_or_client,
)
from app.core.enums import BookingStatus, UserRole

# CRUD imports (explícitos)
from app.crud.crud_booking import booking as booking_crud
from app.crud.crud_class_session import class_session as class_session_crud
from app.crud.crud_client import client as client_crud
from app.db.session import get_async_session

# Schemas importados explícitamente para response_model y tipos
from app.schemas.booking import (
    BookingCreate,
    BookingCreateInternal,
    BookingPublic,
    BookingUpdate,
)
from app.schemas.front_desk import SessionCapacity

# Services
from app.services.booking_service import (
    to_booking_internal,
    to_booking_public,
    validate_booking_creation,
)
from app.services.class_schedule_service import validate_membership_access
from app.services.class_session_service import update_session_availability

# Errores de dominio centralizados
from app.services.errors import BusinessValidationError, ConflictError, NotFoundError

logger = logging.getLogger("fitflow.bookings")
router = APIRouter(prefix="/bookings", tags=["bookings"])

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User

# ruff:noqa: UP037
# --------------------------------------------------------------------------- #
# Crear Booking (cliente)
# --------------------------------------------------------------------------- #
@router.post("/", response_model=BookingPublic, status_code=status.HTTP_201_CREATED)
async def create_booking(  # noqa: C901
    *,
    db: Annotated["AsyncSession", Depends(get_async_session)],
    booking_in: BookingCreate,
    current_user: Annotated["User", Depends(require_admin_or_client)],
) -> BookingPublic:
    """Crea una reserva para una sesión.

    Solo clientes y administradores pueden reservar.
    """
    try:
        session = await class_session_crud.get(
            db=db,
            obj_id=booking_in.class_session_id,  # pyright: ignore[reportArgumentType]
            include_relations=True,
        )
    except Exception as exc:
        logger.exception("DB error fetching class_session for booking creation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La sesión no existe.")

    # Actualizar disponibilidad (pure function)
    try:
        session = update_session_availability(session)
    except Exception as exc:
        logger.exception("Error updating session availability for session_id=%s", getattr(session, "id", None))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    try:
        client = await client_crud.get_by_user_id(
            db=db, user_id=current_user.id, include_relations=True,  # pyright: ignore[reportArgumentType]
        )
    except Exception as exc:
        logger.exception("DB error fetching client for user_id=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    membership = client.membership

    # Validaciones de negocio (pueden lanzar BusinessValidationError)
    try:
        validate_booking_creation(session, membership)
        validate_membership_access(membership, session.class_schedule)
    except BusinessValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Business validation error during booking creation for user=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede crear la reserva") from exc

    # Construir objeto interno para el CRUD atómico
    booking_internal: BookingCreateInternal = to_booking_internal(
        client_id=client.id,  # pyright: ignore[reportArgumentType]
        session=session,
        status=BookingStatus.confirmed,
    )

    try:
        # Llamada atómica al CRUD: verifica cupo y duplicado dentro de una transacción
        booking_obj = await booking_crud.create_with_capacity_check(
            db=db,
            client_id=client.id,  # pyright: ignore[reportArgumentType]
            session_id=session.id,  # pyright: ignore[reportArgumentType]
            obj_in=booking_internal,  # BookingCreateInternal
        )
    except NotFoundError as exc:
        # Si la sesión desapareció entre checks
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        # Duplicado u overbooking detectado en la transacción
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except BusinessValidationError as exc:
        # Validaciones de negocio que el CRUD pudiera propagar
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("DB error creating booking for client=%s session=%s", client.id, session.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return to_booking_public(booking_obj)


# --------------------------------------------------------------------------- #
# Reservas del cliente actual
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=list[BookingPublic])
async def read_my_bookings(
    *,
    db: Annotated["AsyncSession", Depends(get_async_session)],
    current_user: Annotated["User", Depends(require_admin_or_client)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas del cliente autenticado."""
    try:
        client = await client_crud.get_by_user_id(db=db, user_id=current_user.id, include_relations=True)  # pyright: ignore[reportArgumentType]
    except Exception as exc:
        logger.exception("DB error fetching client for read_my_bookings user=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            client_id=client.id,
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings for client=%s", client.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Cancelar reserva
# --------------------------------------------------------------------------- #
@router.post("/{booking_id}/cancel", response_model=BookingPublic)
async def cancel_booking(
    *,
    booking_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
    current_user: Annotated["User", Depends(require_admin_client_or_self)],
) -> BookingPublic:
    """Cancela una reserva existente.

    Los clientes solo pueden cancelar sus propias reservas.
    """
    try:
        booking_obj = await booking_crud.get(db=db, obj_id=booking_id, include_relations=True)
    except Exception as exc:
        logger.exception("DB error fetching booking id=%s", booking_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not booking_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada.")

    try:
        client = await client_crud.get_by_user_id(db=db, user_id=current_user.id)  # pyright: ignore[reportArgumentType]
    except Exception as exc:
        logger.exception("DB error fetching client for cancel_booking user=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    if current_user.role == UserRole.client and booking_obj.client_id != client.id:  # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes cancelar reservas de otros clientes.")

    try:
        updated = await booking_crud.update(
            db=db,
            db_obj=booking_obj,
            obj_in=BookingUpdate(status=BookingStatus.cancelled),
        )
    except Exception as exc:
        logger.exception("DB error updating booking id=%s to cancelled", booking_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return to_booking_public(updated)


# --------------------------------------------------------------------------- #
# Verificar si se puede reservar una sesión
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/can-book", response_model=SessionCapacity)
async def can_book_session(
    *,
    session_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> SessionCapacity:
    """Devuelve la capacidad disponible de una sesión.

    Útil para validar si un cliente puede reservar.
    """
    try:
        session = await class_session_crud.get(db=db, obj_id=session_id, include_relations=True)
    except Exception as exc:
        logger.exception("DB error fetching class_session id=%s", session_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ClassSession no encontrada.")

    try:
        session = update_session_availability(session)
    except Exception as exc:
        logger.exception("Error updating session availability for session_id=%s", session_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return SessionCapacity(
        session_id=session.id,  # pyright: ignore[reportArgumentType]
        capacity=session.class_schedule.capacity,  # pyright: ignore[reportArgumentType]
        used=session.current_bookings_count,
        available=session.available_spots,
    )


# --------------------------------------------------------------------------- #
# Reservas públicas por sesión
# --------------------------------------------------------------------------- #
@router.get("/sessions/{session_id}/public", response_model=list[BookingPublic])
async def read_session_bookings_public(
    *,
    session_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas públicas de una sesión."""
    try:
        session = await class_session_crud.get(db=db, obj_id=session_id, include_relations=True)
    except Exception as exc:
        logger.exception("DB error fetching class_session id=%s for public bookings", session_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ClassSession no encontrada.")

    return [to_booking_public(b) for b in session.bookings]


# --------------------------------------------------------------------------- #
# Reservas públicas por clase
# --------------------------------------------------------------------------- #
@router.get("/classes/{class_id}/public", response_model=list[BookingPublic])
async def read_class_bookings_public(
    *,
    class_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas públicas asociadas a una clase."""
    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            class_id=class_id,  # pyright: ignore[reportCallIssue]
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings for class_id=%s", class_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas públicas por horario
# --------------------------------------------------------------------------- #
@router.get("/class-schedules/{schedule_id}/public", response_model=list[BookingPublic])
async def read_schedule_bookings_public(
    *,
    schedule_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas públicas asociadas a un horario."""
    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            schedule_id=schedule_id,  # pyright: ignore[reportCallIssue]
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings for schedule_id=%s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por día
# --------------------------------------------------------------------------- #
@router.get("/day", response_model=list[BookingPublic])
async def read_bookings_by_day(
    *,
    date_query: "date",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas realizadas en un día específico."""
    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            date=date_query,  # pyright: ignore[reportCallIssue]
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings by day=%s", date_query)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por rango
# --------------------------------------------------------------------------- #
@router.get("/range", response_model=list[BookingPublic])
async def read_bookings_by_range(
    *,
    date_from: "date",
    date_to: "date",
    db: Annotated["AsyncSession", Depends(get_async_session)],
) -> list[BookingPublic]:
    """Devuelve todas las reservas dentro de un rango de fechas."""
    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            date_from=date_from,
            date_to=date_to,
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings by range %s - %s", date_from, date_to)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]


# --------------------------------------------------------------------------- #
# Reservas por cliente (admin)
# --------------------------------------------------------------------------- #
@router.get("/client/{client_id}", response_model=list[BookingPublic])
async def read_bookings_by_client(
    *,
    client_id: "UUID",
    db: Annotated["AsyncSession", Depends(get_async_session)],
    current_user: Annotated["User", Depends(require_admin)],  # noqa: ARG001
) -> list[BookingPublic]:
    """Devuelve todas las reservas de un cliente específico.

    Solo administradores pueden acceder.
    """
    try:
        bookings = await booking_crud.get_multi_filtered(
            db=db,
            client_id=client_id,
            include_relations=True,  # pyright: ignore[reportCallIssue]
        )
    except Exception as exc:
        logger.exception("DB error fetching bookings for client_id=%s", client_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    return [to_booking_public(b) for b in bookings]

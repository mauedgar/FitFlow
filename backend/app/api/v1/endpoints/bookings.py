"""
Endpoints para Booking (asíncrono, Sprint 5)
--------------------------------------------
• Reserva de sesiones de clases por parte de clientes.
• Validaciones: capacidad, duplicados, estado de sesión, rol cliente.
• Carga selectiva de relaciones (client, class_session → schedule → gym_class).
"""

from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app import crud, schemas
from app.models import Booking, ClassSession, User, UserRole

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ------------------------------------------------------------------ #
# Crear Booking
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.Booking, status_code=status.HTTP_201_CREATED)
async def create_booking(
    *,
    db: AsyncSession = Depends(get_async_session),
    booking_in: schemas.BookingCreate,
    current_user: User = Depends(crud.user.get_current_active_client),
):
    """
    Crea una reserva para una sesión de clase.
    Requiere rol CLIENT.
    """

    # 1. Validar sesión
    session = await crud.class_session.get(db, id=booking_in.class_session_id, include_relations=True)
    if not session:
        raise HTTPException(404, "La sesión no existe.")

    # 2. Validar capacidad
    current_bookings = len(session.bookings)
    if current_bookings >= session.capacity_snapshot:
        raise HTTPException(400, "La sesión está llena.")

    # 3. Validar duplicado
    existing = await crud.booking.get_multi_filtered(
        db=db,
        client_id=current_user.person_profile.id,
        session_id=session.id,
    )
    if existing:
        raise HTTPException(400, "Ya tienes una reserva para esta sesión.")

    # 4. Crear reserva
    booking = await crud.booking.create(
        db=db,
        obj_in=schemas.BookingCreateInternal(
            client_id=current_user.person_profile.id,
            class_session_id=session.id,
        ),
    )

    return booking


# ------------------------------------------------------------------ #
# Listar Bookings (admin)
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Booking])
async def read_bookings(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: User = Depends(crud.user.get_current_admin),
):
    bookings = await crud.booking.get_multi_filtered(
        db=db,
        client_id=client_id,
        session_id=session_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return bookings


# ------------------------------------------------------------------ #
# Obtener Booking por ID
# ----------------------------------------------------------------
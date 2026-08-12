"""Router ClassSession (Sprint 6-7).

--------------------------------
• CRUD de sesiones concretas.
• Endpoints operativos y públicos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import require_admin, require_admin_or_front_desk
from app.core.enums import ClassSessionStatus
from app.core.timezone import LOCAL_TZ
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_class_session import class_session
from app.db.session import get_async_session
from backend.app.db.models.class_schedule import ClassSchedule
from backend.app.db.models.class_session import ClassSession
from app.services.class_session_service import (
    to_class_session_response,
    update_session_availability,
)
from app.schemas.class_session import (
    ClassSessionCreate,
    ClassSessionInResponse,
    ClassSessionUpdate,
)
from app.schemas.front_desk import SessionCapacity

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from backend.app.db.models.user import User

router = APIRouter(prefix="/class-sessions", tags=["class-sessions"])


# --------------------------------------------------------------------------- #
# Crear sesión (admin)
# --------------------------------------------------------------------------- #
@router.post("/", response_model=ClassSessionInResponse, status_code=status.HTTP_201_CREATED)
async def create_class_session(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_in: ClassSessionCreate,
    _: Annotated[User, Depends(require_admin)],
) -> ClassSessionInResponse:
    """Crea una nueva sesión de clase."""
    schedule = await class_schedule.get(db, obj_id=session_in.class_schedule_id)
    if not schedule:
        raise HTTPException(404, "ClassSchedule no encontrado.")

    session = await class_session.create(db=db, obj_in=session_in)
    session = update_session_availability(session)
    return to_class_session_response(session)


# --------------------------------------------------------------------------- #
# Listar sesiones con filtros (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[ClassSessionInResponse])
async def read_class_sessions(  # noqa: PLR0913
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 100,
    schedule_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[ClassSessionInResponse]:
    """Devuelve todas las sesiones filtradas por clase o rango de fechas."""
    stmt = (
        select(ClassSession)
        .options(
            selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.gym_class),
            selectinload(ClassSession.bookings),
        )
        .order_by(ClassSession.starts_at)
        .offset(skip)
        .limit(limit)
    )

    if schedule_id:
        stmt = stmt.where(ClassSession.class_schedule_id == schedule_id)
    if date_from:
        start_dt = datetime.combine(date_from, datetime.min.time(), tzinfo=LOCAL_TZ)
        stmt = stmt.where(ClassSession.starts_at >= start_dt)
    if date_to:
        end_dt = datetime.combine(date_to, datetime.max.time(), tzinfo=LOCAL_TZ)
        stmt = stmt.where(ClassSession.starts_at <= end_dt)

    res = await db.execute(stmt)
    sessions = res.scalars().unique().all()
    return [to_class_session_response(update_session_availability(s)) for s in sessions]


# --------------------------------------------------------------------------- #
# Obtener sesión por ID (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{session_id}", response_model=ClassSessionInResponse)
async def read_class_session_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_id: UUID,
) -> ClassSessionInResponse:
    """Obtiene una sesión específica por su ID."""
    session = await class_session.get(db, obj_id=session_id, include_relations=True)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    session = update_session_availability(session)
    return to_class_session_response(session)


# --------------------------------------------------------------------------- #
# Actualizar sesión (admin)
# --------------------------------------------------------------------------- #
@router.put("/{session_id}", response_model=ClassSessionInResponse)
async def update_class_session(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_id: UUID,
    session_in: ClassSessionUpdate,
    _: Annotated[User, Depends(require_admin)],
) -> ClassSessionInResponse:
    """Actualiza los datos de una sesión existente."""
    session = await class_session.get(db, obj_id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    updated = await class_session.update(db=db, db_obj=session, obj_in=session_in)
    updated = update_session_availability(updated)
    return to_class_session_response(updated)


# --------------------------------------------------------------------------- #
# Eliminar sesión (admin)
# --------------------------------------------------------------------------- #
@router.delete("/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_class_session(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    session_id: UUID,
    _: Annotated[User, Depends(require_admin)],
) -> dict[str, str]:
    """Elimina una sesión existente."""
    session = await class_session.get(db, obj_id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    await class_session.remove(db, db_obj=session)

    return {"message": "Sesión eliminada exitosamente."}


# --------------------------------------------------------------------------- #
# Cancelar sesión (operativo)
# --------------------------------------------------------------------------- #
@router.post("/{session_id}/cancel", response_model=ClassSessionInResponse)
async def cancel_class_session(
    *,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _: Annotated[User, Depends(require_admin_or_front_desk)],
) -> ClassSessionInResponse:
    """Cancela una sesión (status = cancelled)."""
    session = await class_session.get(db, obj_id=session_id)
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
# Disponibilidad de sesión (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{session_id}/availability", response_model=SessionCapacity)
async def get_session_availability(
    *,
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> SessionCapacity:
    """Devuelve la capacidad disponible de una sesión."""
    session = await class_session.get(db, obj_id=session_id, include_relations=True)
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
# Sesiones públicas por clase
# --------------------------------------------------------------------------- #
@router.get("/class/{class_id}/public", response_model=list[ClassSessionInResponse])
async def read_sessions_by_class_public(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSessionInResponse]:
    """Devuelve las sesiones públicas asociadas a una clase."""
    sessions = await class_session.get_multi_filtered(db=db, schedule_id=class_id, include_relations=True)
    return [to_class_session_response(update_session_availability(s)) for s in sessions]


# --------------------------------------------------------------------------- #
# Sesiones públicas por profesor
# --------------------------------------------------------------------------- #
@router.get("/teacher/{teacher_id}/public", response_model=list[ClassSessionInResponse])
async def read_sessions_by_teacher_public(
    *,
    teacher_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSessionInResponse]:
    """Devuelve las sesiones públicas asociadas a un profesor."""
    sessions = await class_session.get_multi_filtered(db=db, teacher_id=teacher_id, include_relations=True)
    return [to_class_session_response(update_session_availability(s)) for s in sessions]


# --------------------------------------------------------------------------- #
# Sesiones públicas por día
# --------------------------------------------------------------------------- #
@router.get("/day", response_model=list[ClassSessionInResponse])
async def read_sessions_by_day(
    *,
    date_query: date,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSessionInResponse]:
    """Devuelve las sesiones públicas correspondientes a un día específico."""
    start_dt = datetime.combine(date_query, datetime.min.time(), tzinfo=LOCAL_TZ)
    end_dt = datetime.combine(date_query, datetime.max.time(), tzinfo=LOCAL_TZ)

    sessions = await class_session.get_multi_filtered(
        db=db,
        date_from=start_dt,
        date_to=end_dt,
        include_relations=True,
    )
    return [to_class_session_response(update_session_availability(s)) for s in sessions]

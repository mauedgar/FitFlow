"""
Endpoints para ClassSession (asíncrono, Sprint 5)
-------------------------------------------------
• CRUD completo para sesiones concretas.
• Filtros avanzados: schedule_id, rango de fechas.
• Carga selectiva de relaciones (schedule, bookings).
• Compatible con generación automática desde ClassSchedule.
"""

from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app import crud, schemas
from app.models import ClassSession, ClassSchedule, User, UserRole

router = APIRouter(prefix="/class-sessions", tags=["class-sessions"])


# ------------------------------------------------------------------ #
# Crear ClassSession
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.ClassSession, status_code=status.HTTP_201_CREATED)
async def create_class_session(
    *,
    db: AsyncSession = Depends(get_async_session),
    session_in: schemas.ClassSessionCreate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    schedule = await crud.class_schedule.get(db, id=session_in.schedule_id)
    if not schedule:
        raise HTTPException(404, "ClassSchedule no encontrado.")

    session = await crud.class_session.create(db=db, obj_in=session_in)
    return session


# ------------------------------------------------------------------ #
# Listar ClassSessions con filtros
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.ClassSession])
async def read_class_sessions(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    schedule_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    stmt = (
        select(ClassSession)
        .options(
            selectinload(ClassSession.schedule),
            selectinload(ClassSession.bookings),
        )
        .order_by(ClassSession.start_datetime)
        .offset(skip)
        .limit(limit)
    )

    if schedule_id:
        stmt = stmt.where(ClassSession.schedule_id == schedule_id)

    if date_from:
        stmt = stmt.where(ClassSession.start_datetime >= datetime.combine(date_from, datetime.min.time()))

    if date_to:
        stmt = stmt.where(ClassSession.start_datetime <= datetime.combine(date_to, datetime.max.time()))

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# ------------------------------------------------------------------ #
# Obtener ClassSession por ID
# ------------------------------------------------------------------ #
@router.get("/{session_id}", response_model=schemas.ClassSession)
async def read_class_session_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    session_id: UUID,
):
    stmt = (
        select(ClassSession)
        .where(ClassSession.id == session_id)
        .options(
            selectinload(ClassSession.schedule),
            selectinload(ClassSession.bookings),
        )
    )

    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    return session


# ------------------------------------------------------------------ #
# Actualizar ClassSession
# ------------------------------------------------------------------ #
@router.put("/{session_id}", response_model=schemas.ClassSession)
async def update_class_session(
    *,
    db: AsyncSession = Depends(get_async_session),
    session_id: UUID,
    session_in: schemas.ClassSessionUpdate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    session = await crud.class_session.get(db, id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    updated = await crud.class_session.update(db, db_obj=session, obj_in=session_in)
    return updated


# ------------------------------------------------------------------ #
# Eliminar ClassSession
# ------------------------------------------------------------------ #
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_session(
    *,
    db: AsyncSession = Depends(get_async_session),
    session_id: UUID,
    current_user: User = Depends(crud.user.get_current_admin),
):
    session = await crud.class_session.get(db, id=session_id)
    if not session:
        raise HTTPException(404, "ClassSession no encontrada.")

    await crud.class_session.remove(db, id=session_id)
    return {"message": "Sesión eliminada exitosamente."}

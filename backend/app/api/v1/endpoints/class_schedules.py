"""
Endpoints para ClassSchedule (asíncrono, Sprint 5)
--------------------------------------------------
• CRUD completo para horarios recurrentes.
• Validación de gym_class y teacher antes de crear.
• Filtros avanzados: gym_class_id, teacher_id, day_of_week.
• Carga selectiva de relaciones (gym_class, teacher, sessions).
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
from app.models import ClassSchedule, ClassSession, User, UserRole

router = APIRouter(prefix="/class-schedules", tags=["class-schedules"])


# ------------------------------------------------------------------ #
# Crear ClassSchedule
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.ClassSchedule, status_code=status.HTTP_201_CREATED)
async def create_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_in: schemas.ClassScheduleCreate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    """
    Crea un horario recurrente para una clase.
    Requiere permisos de administrador.
    """
    gym_class = await crud.gym_class.get(db, id=schedule_in.gym_class_id)
    if not gym_class:
        raise HTTPException(404, f"GymClass {schedule_in.gym_class_id} no existe.")

    teacher = await crud.teacher.get(db, id=schedule_in.teacher_id)
    if not teacher:
        raise HTTPException(404, f"Teacher {schedule_in.teacher_id} no existe.")

    schedule = await crud.class_schedule.create(db=db, obj_in=schedule_in)
    return schedule


# ------------------------------------------------------------------ #
# Listar ClassSchedules con filtros
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.ClassSchedule])
async def read_class_schedules(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    gym_class_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
    day_of_week: Optional[int] = None,
):
    """
    Lista horarios recurrentes con filtros opcionales.
    """
    stmt = (
        select(ClassSchedule)
        .options(
            selectinload(ClassSchedule.gym_class),
            selectinload(ClassSchedule.teacher),
            selectinload(ClassSchedule.sessions),
        )
        .order_by(ClassSchedule.start_time)
        .offset(skip)
        .limit(limit)
    )

    if gym_class_id:
        stmt = stmt.where(ClassSchedule.gym_class_id == gym_class_id)

    if teacher_id:
        stmt = stmt.where(ClassSchedule.teacher_id == teacher_id)

    if day_of_week is not None:
        stmt = stmt.where(ClassSchedule.days_of_week.contains([day_of_week]))

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# ------------------------------------------------------------------ #
# Obtener ClassSchedule por ID
# ------------------------------------------------------------------ #
@router.get("/{schedule_id}", response_model=schemas.ClassSchedule)
async def read_class_schedule_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
):
    stmt = (
        select(ClassSchedule)
        .where(ClassSchedule.id == schedule_id)
        .options(
            selectinload(ClassSchedule.gym_class),
            selectinload(ClassSchedule.teacher),
            selectinload(ClassSchedule.sessions),
        )
    )

    res = await db.execute(stmt)
    schedule = res.scalars().first()

    if not schedule:
        raise HTTPException(404, f"ClassSchedule {schedule_id} no encontrado.")

    return schedule


# ------------------------------------------------------------------ #
# Actualizar ClassSchedule
# ------------------------------------------------------------------ #
@router.put("/{schedule_id}", response_model=schemas.ClassSchedule)
async def update_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
    schedule_in: schemas.ClassScheduleUpdate,
    current_user: User = Depends(crud.user.get_current_admin),
):
    schedule = await crud.class_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado.")

    updated = await crud.class_schedule.update(db, db_obj=schedule, obj_in=schedule_in)
    return updated


# ------------------------------------------------------------------ #
# Eliminar ClassSchedule
# ------------------------------------------------------------------ #
@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
    current_user: User = Depends(crud.user.get_current_admin),
):
    schedule = await crud.class_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado.")

    await crud.class_schedule.remove(db, id=schedule_id)
    return {"message": "Horario eliminado exitosamente."}

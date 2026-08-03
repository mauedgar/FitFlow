"""
Router ClassSchedule (Sprint 6–7)
---------------------------------
• CRUD de horarios recurrentes.
• Endpoints públicos y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""
# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID

from app import crud, schemas
from app.api.deps import require_admin
from app.db.session import get_async_session
from app.models.class_schedule import ClassSchedule
from app.models.user import User
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/class-schedules", tags=["class-schedules"])


# --------------------------------------------------------------------------- #
# Crear horario
# --------------------------------------------------------------------------- #
@router.post("/", response_model=schemas.ClassSchedule, status_code=status.HTTP_201_CREATED)
async def create_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_in: schemas.ClassScheduleCreate,
    current_user: User = Depends(require_admin),
):
    """Crea un horario recurrente para una clase."""
    gym_class = await crud.gym_class.get(db, id=schedule_in.gym_class_id)
    if not gym_class:
        raise HTTPException(404, f"GymClass {schedule_in.gym_class_id} no existe.")

    teacher = await crud.teacher.get(db, id=schedule_in.teacher_id)
    if not teacher:
        raise HTTPException(404, f"Teacher {schedule_in.teacher_id} no existe.")

    schedule = await crud.class_schedule.create(db=db, obj_in=schedule_in)
    return schedule


# --------------------------------------------------------------------------- #
# Listar horarios (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[schemas.ClassSchedule])
async def read_class_schedules(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    gym_class_id: UUID | None = None,
    teacher_id: UUID | None = None,
    day_of_week: int | None = None,
):
    """Lista horarios con filtros operativos."""
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


# --------------------------------------------------------------------------- #
# Obtener horario por ID (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{schedule_id}", response_model=schemas.ClassSchedule)
async def read_class_schedule_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
):
    """Obtiene un horario por ID."""
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


# --------------------------------------------------------------------------- #
# Actualizar horario
# --------------------------------------------------------------------------- #
@router.put("/{schedule_id}", response_model=schemas.ClassSchedule)
async def update_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
    schedule_in: schemas.ClassScheduleUpdate,
    current_user: User = Depends(require_admin),
):
    """Actualiza un horario."""
    schedule = await crud.class_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado.")

    updated = await crud.class_schedule.update(db, db_obj=schedule, obj_in=schedule_in)
    return updated


# --------------------------------------------------------------------------- #
# Eliminar horario
# --------------------------------------------------------------------------- #
@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    schedule_id: UUID,
    current_user: User = Depends(require_admin),
):
    """Elimina un horario."""
    schedule = await crud.class_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado.")

    await crud.class_schedule.remove(db, id=schedule_id)
    return {"message": "Horario eliminado exitosamente."}


# --------------------------------------------------------------------------- #
# Horarios públicos
# --------------------------------------------------------------------------- #
@router.get("/public", response_model=list[schemas.ClassSchedulePublic])
async def read_public_schedules(
    *,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista horarios públicos."""
    schedules = await crud.class_schedule.get_multi(db)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios públicos por clase
# --------------------------------------------------------------------------- #
@router.get("/class/{class_id}/public", response_model=list[schemas.ClassSchedulePublic])
async def read_public_schedules_by_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista horarios públicos de una clase."""
    schedules = await crud.class_schedule.get_multi_filtered(db, gym_class_id=class_id)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios públicos por profesor
# --------------------------------------------------------------------------- #
@router.get("/teacher/{teacher_id}/public", response_model=list[schemas.ClassSchedulePublic])
async def read_public_schedules_by_teacher(
    *,
    teacher_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista horarios públicos de un profesor."""
    schedules = await crud.class_schedule.get_multi_filtered(db, teacher_id=teacher_id)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Próxima sesión de un horario
# --------------------------------------------------------------------------- #
@router.get("/{schedule_id}/next-session", response_model=schemas.NextSessionInfo | None)
async def read_next_session(
    *,
    schedule_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Devuelve la próxima sesión futura de un horario."""
    schedule = await crud.class_schedule.get(db, id=schedule_id, include_relations=True)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado.")

    return get_next_session(schedule)

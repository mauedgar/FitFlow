"""
Router GymClass (Sprint 6–7)
----------------------------
• CRUD del catálogo de clases.
• Filtros operativos avanzados.
• Versiones públicas y operativas.
• Integración con horarios y sesiones.
"""
# ruff: noqa: B008

from __future__ import annotations

from datetime import date
from uuid import UUID

from app import crud, schemas
from app.db.session import get_async_session
from app.models.class_schedule import ClassSchedule
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)
from app.services.gym_class_service import (
    to_gym_class_public,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/gym-classes", tags=["gym-classes"])


# --------------------------------------------------------------------------- #
# Crear GymClass
# --------------------------------------------------------------------------- #
@router.post("/", response_model=schemas.GymClassRead, status_code=status.HTTP_201_CREATED)
async def create_gym_class(
    *,
    db: AsyncSession = Depends(get_async_session),
    class_in: schemas.GymClassCreate,
):
    """Crea una nueva clase en el catálogo."""
    gym_class = await crud.gym_class.create(db=db, obj_in=class_in)
    return gym_class


# --------------------------------------------------------------------------- #
# Listar GymClasses (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[schemas.GymClassRead])
async def list_gym_classes(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    difficulty: None | str = Query(None),
    activity_type: None | str = Query(None),
    active: None | bool = Query(True),
    search: None | str = Query(None),
    teacher_id: None | UUID = Query(None),
    day_of_week: None | int = Query(None, ge=0, le=6),
    date_from: None | date = Query(None),
    date_to: None | date = Query(None),
    include_schedules: bool = Query(False),
    db: AsyncSession = Depends(get_async_session),
):
    """Lista clases del catálogo con filtros operativos."""
    classes = await crud.gym_class.get_multi_filtered(
        db=db,
        skip=skip,
        limit=limit,
        difficulty=difficulty,
        activity_type=activity_type,
        active=active,
        search=search,
        teacher_id=teacher_id,
        day_of_week=day_of_week,
        date_from=date_from,
        date_to=date_to,
    )

    if not include_schedules:
        return classes

    # Cargar horarios y profesor
    ids = [c.id for c in classes]

    classes_with_sched = await crud.gym_class.get_multi(
        db=db,
        filters={"id": ids},
        options=[
            selectinload(crud.gym_class.model.class_schedules)
            .selectinload(ClassSchedule.teacher)
        ],
    )

    classes_map = {c.id: c for c in classes_with_sched}
    return [classes_map[i] for i in ids]


# --------------------------------------------------------------------------- #
# Obtener GymClass por ID (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{class_id}", response_model=schemas.GymClassRead)
async def read_gym_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Obtiene una clase del catálogo por ID."""
    gym_class = await crud.gym_class.get(
        db,
        id=class_id,
        include_schedules=True,
    )
    if not gym_class:
        raise HTTPException(404, "Clase no encontrada")
    return gym_class


# --------------------------------------------------------------------------- #
# Actualizar GymClass
# --------------------------------------------------------------------------- #
@router.put("/{class_id}", response_model=schemas.GymClassRead)
async def update_gym_class(
    *,
    class_id: UUID,
    class_in: schemas.GymClassUpdate,
    db: AsyncSession = Depends(get_async_session),
):
    """Actualiza una clase del catálogo."""
    gym_class = await crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(404, "Clase no encontrada")

    updated = await crud.gym_class.update(db, db_obj=gym_class, obj_in=class_in)
    return updated


# --------------------------------------------------------------------------- #
# Eliminar GymClass (soft delete)
# --------------------------------------------------------------------------- #
@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gym_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Elimina una clase del catálogo (soft delete)."""
    gym_class = await crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(404, "Clase no encontrada")

    await crud.gym_class.remove(db, db_obj=gym_class)
    return {"detail": "GymClass eliminada"}


# --------------------------------------------------------------------------- #
# Listado público de clases
# --------------------------------------------------------------------------- #
@router.get("/public", response_model=list[schemas.GymClassPublic])
async def list_public_gym_classes(
    *,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista pública del catálogo de clases."""
    classes = await crud.gym_class.get_multi(db)
    return [to_gym_class_public(c) for c in classes]


# --------------------------------------------------------------------------- #
# Clase pública por ID
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/public", response_model=schemas.GymClassPublic)
async def read_public_gym_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Obtiene una clase en versión pública."""
    gym_class = await crud.gym_class.get(db, id=class_id, include_schedules=True)
    if not gym_class:
        raise HTTPException(404, "Clase no encontrada")

    return to_gym_class_public(gym_class)


# --------------------------------------------------------------------------- #
# Horarios públicos de una clase
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/schedules/public", response_model=list[schemas.ClassSchedulePublic])
async def read_public_class_schedules(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista horarios públicos de una clase."""
    schedules = await crud.class_schedule.get_multi_filtered(db, gym_class_id=class_id)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Próxima sesión de una clase
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/next-session", response_model=schemas.NextSessionInfo | None)
async def read_class_next_session(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Devuelve la próxima sesión futura de una clase."""
    schedules = await crud.class_schedule.get_multi_filtered(
        db,
        gym_class_id=class_id,
        include_relations=True,
    )

    next_sessions = [get_next_session(s) for s in schedules]
    next_sessions = [ns for ns in next_sessions if ns is not None]

    if not next_sessions:
        return None

    return min(next_sessions, key=lambda ns: ns.starts_at)


# --------------------------------------------------------------------------- #
# Clases públicas impartidas por un profesor
# --------------------------------------------------------------------------- #
@router.get("/teacher/{teacher_id}/public", response_model=list[schemas.GymClassPublic])
async def read_public_classes_by_teacher(
    *,
    teacher_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista clases públicas impartidas por un profesor."""
    classes = await crud.gym_class.get_multi_filtered(db, teacher_id=teacher_id)
    return [to_gym_class_public(c) for c in classes]


# --------------------------------------------------------------------------- #
# Clases públicas por día de la semana
# --------------------------------------------------------------------------- #
@router.get("/day/{day_of_week}/public", response_model=list[schemas.GymClassPublic])
async def read_public_classes_by_day(
    *,
    day_of_week: int,
    db: AsyncSession = Depends(get_async_session),
):
    """Lista clases públicas que tienen horarios en un día específico."""
    schedules = await crud.class_schedule.get_multi_filtered(
        db,
        day_of_week=day_of_week,
        include_relations=True,
    )
    classes = {s.gym_class for s in schedules}
    return [to_gym_class_public(c) for c in classes]

from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import crud, schemas
from app.db.session import get_async_session
from app.models.class_schedule import ClassSchedule

router = APIRouter(prefix="/gym-classes", tags=["gym-classes"])

# --------------------------------------------------------------------------- #
# CREATE
# --------------------------------------------------------------------------- #
@router.post(
    "/",
    response_model=schemas.GymClassRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_gym_class(
    *,
    db: AsyncSession = Depends(get_async_session),
    class_in: schemas.GymClassCreate,
):
    """
    Crea una nueva GymClass (catálogo de actividades).
    """
    gym_class = await crud.gym_class.create(db=db, obj_in=class_in)
    return gym_class


# --------------------------------------------------------------------------- #
# LIST + FILTROS
# --------------------------------------------------------------------------- #
@router.get("/", response_model=List[schemas.GymClassRead])
async def list_gym_classes(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    difficulty: Optional[str] = Query(None, description="beginner|intermediate|advanced"),
    activity_type: Optional[str] = Query(None),
    active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None, description="Búsqueda por nombre / descripción"),
    teacher_id: Optional[UUID] = Query(None),
    day_of_week: Optional[int] = Query(None, ge=0, le=6),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    include_schedules: bool = Query(False, description="Incluir schedules en la respuesta"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Devuelve el catálogo de GymClasses con filtros opcionales.
    """
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

    # Si no se piden schedules, devolvemos tal cual
    if not include_schedules:
        return classes

    # Cargar schedules con selectinload para evitar N+1
    ids = [c.id for c in classes]
    classes_with_sched = await crud.gym_class.get_multi(
        db=db,
        filters={"id": ids},
        options=[selectinload(crud.gym_class.model.class_schedules).selectinload(ClassSchedule.teacher)],
    )
    # Mantener el orden original
    classes_map = {c.id: c for c in classes_with_sched}
    return [classes_map[i] for i in ids]


# --------------------------------------------------------------------------- #
# RETRIEVE
# --------------------------------------------------------------------------- #
@router.get(
    "/{class_id}",
    response_model=schemas.GymClassRead,
)
async def read_gym_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Obtiene una GymClass por ID con sus ClassSchedules (profesor incluido).
    """
    gym_class = await crud.gym_class.get(
        db,
        id=class_id,
        include_schedules=True,
    )
    if not gym_class:
        raise HTTPException(status_code=404, detail="Clase no encontrada")
    return gym_class


# --------------------------------------------------------------------------- #
# UPDATE
# --------------------------------------------------------------------------- #
@router.put("/{class_id}", response_model=schemas.GymClassRead)
async def update_gym_class(
    *,
    class_id: UUID,
    class_in: schemas.GymClassUpdate,
    db: AsyncSession = Depends(get_async_session),
):
    gym_class = await crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    updated = await crud.gym_class.update(db, db_obj=gym_class, obj_in=class_in)
    return updated


# --------------------------------------------------------------------------- #
# DELETE (soft)
# --------------------------------------------------------------------------- #
@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gym_class(
    *,
    class_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    gym_class = await crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    await crud.gym_class.remove(db, db_obj=gym_class)  # soft-delete
    return {"detail": "GymClass eliminada"}
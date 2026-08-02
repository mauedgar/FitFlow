"""
Endpoints para Teacher (asíncrono, Sprint 5)
--------------------------------------------
• CRUD completo para perfiles de profesores.
• Validación estricta de roles (admin / self).
• Carga selectiva de relaciones (class_schedules → gym_class).
• Uso de AsyncSession + select() + selectinload().
"""

from __future__ import annotations
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app import crud, schemas
from app.models import Teacher, ClassSchedule, User, UserRole
from app.api.deps import (
    get_current_active_user,
    get_current_admin,
)

router = APIRouter(prefix="/teachers", tags=["teachers"])


# ------------------------------------------------------------------ #
# Crear Teacher para un User existente
# ------------------------------------------------------------------ #
@router.post("/{user_id}", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
async def create_teacher_for_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: UUID,
    teacher_in: schemas.TeacherCreate,
    current_user: User = Depends(get_current_admin),
):
    """
    Crea un perfil de profesor para un usuario existente.
    Requiere permisos de administrador.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"El usuario {user_id} no existe.")

    if user.person_profile:
        raise HTTPException(status_code=400, detail="El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=400,
            detail=f"El usuario no tiene rol '{UserRole.TEACHER}'. Actualiza el rol primero.",
        )

    teacher = await crud.teacher.create_with_user(db=db, obj_in=teacher_in, user=user)
    return teacher


# ------------------------------------------------------------------ #
# Listar Teachers
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Teacher])
async def read_teachers(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
):
    """
    Obtiene una lista de profesores con sus horarios y clases asociadas.
    """
    stmt = (
        select(Teacher)
        .options(
            selectinload(Teacher.class_schedules)
            .selectinload(ClassSchedule.gym_class)
        )
        .offset(skip)
        .limit(limit)
    )

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# ------------------------------------------------------------------ #
# Obtener Teacher por ID
# ------------------------------------------------------------------ #
@router.get("/{teacher_id}", response_model=schemas.Teacher)
async def read_teacher_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """
    Obtiene los detalles de un profesor por ID.
    Incluye horarios y clases asociadas.
    """
    stmt = (
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(
            selectinload(Teacher.class_schedules)
            .selectinload(ClassSchedule.gym_class)
        )
    )

    res = await db.execute(stmt)
    teacher = res.scalars().first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado.")

    return teacher
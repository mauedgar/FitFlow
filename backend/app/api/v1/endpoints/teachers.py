"""
Router Teacher (Sprint 6–7)
---------------------------
• CRUD de perfiles de profesores.
• Endpoints públicos y operativos.
• Integración con horarios y sesiones.
• Lógica centralizada en services.
"""
# ruff: noqa: B008

from __future__ import annotations

from uuid import UUID

from app import crud, schemas
from app.api.deps import (
    require_admin,
    require_admin_or_teacher,
    require_admin_teacher_or_self,
)
from app.db.session import get_async_session
from app.models.class_schedule import ClassSchedule
from app.models.teacher import Teacher
from app.models.user import User, UserRole
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)
from app.services.class_session_service import (
    to_class_session_response,
    update_session_availability,
)
from app.services.teacher_service import (
    to_teacher_public,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/teachers", tags=["teachers"])


# --------------------------------------------------------------------------- #
# Crear Teacher para un User existente
# --------------------------------------------------------------------------- #
@router.post("/{user_id}", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
async def create_teacher_for_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: UUID,
    teacher_in: schemas.TeacherCreate,
    current_user: User = Depends(require_admin),
):
    """Crea un perfil de profesor para un usuario existente."""
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(404, f"El usuario {user_id} no existe.")

    if user.person_profile:
        raise HTTPException(400, "El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.teacher:
        raise HTTPException(400, f"El usuario no tiene rol '{UserRole.teacher}'.")

    teacher = await crud.teacher.create_with_user(db=db, obj_in=teacher_in, user=user)
    return teacher


# --------------------------------------------------------------------------- #
# Listar Teachers (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[schemas.Teacher])
async def read_teachers(
    *,
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin_or_teacher),
):
    """Lista profesores con horarios y clases asociadas (operativo)."""
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


# --------------------------------------------------------------------------- #
# Listar Teachers (público)
# --------------------------------------------------------------------------- #
@router.get("/public", response_model=list[schemas.TeacherPublic])
async def read_public_teachers(
    db: AsyncSession = Depends(get_async_session),
):
    """Lista profesores en versión pública."""
    stmt = (
        select(Teacher)
        .options(
            selectinload(Teacher.class_schedules)
            .selectinload(ClassSchedule.gym_class)
        )
    )

    res = await db.execute(stmt)
    teachers = res.scalars().unique().all()

    return [to_teacher_public(t) for t in teachers]


# --------------------------------------------------------------------------- #
# Obtener Teacher por ID (privado)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}", response_model=schemas.Teacher)
async def read_teacher_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    current_user: User = Depends(require_admin_teacher_or_self),
):
    """Obtiene detalles privados de un profesor."""
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
        raise HTTPException(404, "Profesor no encontrado.")

    return teacher


# --------------------------------------------------------------------------- #
# Obtener Teacher por ID (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/public", response_model=schemas.TeacherPublic)
async def read_teacher_public_by_id(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
):
    """Obtiene detalles públicos de un profesor."""
    teacher = await crud.teacher.get(db, id=teacher_id, include_relations=True)
    if not teacher:
        raise HTTPException(404, "Profesor no encontrado.")

    return to_teacher_public(teacher)


# --------------------------------------------------------------------------- #
# Actualizar Teacher
# --------------------------------------------------------------------------- #
@router.put("/{teacher_id}", response_model=schemas.Teacher)
async def update_teacher(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    teacher_in: schemas.TeacherUpdate,
    current_user: User = Depends(require_admin_teacher_or_self),
):
    """Actualiza perfil privado del profesor."""
    teacher = await crud.teacher.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(404, "Profesor no encontrado.")

    updated = await crud.teacher.update(db, db_obj=teacher, obj_in=teacher_in)
    return updated


# --------------------------------------------------------------------------- #
# Eliminar Teacher
# --------------------------------------------------------------------------- #
@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    current_user: User = Depends(require_admin),
):
    """Elimina un perfil de profesor."""
    teacher = await crud.teacher.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(404, "Profesor no encontrado.")

    await crud.teacher.remove(db, id=teacher_id)


# --------------------------------------------------------------------------- #
# Clases impartidas por el profesor (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/classes", response_model=list[schemas.ClassSchedule])
async def read_teacher_classes(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    current_user: User = Depends(require_admin_or_teacher),
):
    """Lista clases impartidas por el profesor (operativo)."""
    stmt = (
        select(ClassSchedule)
        .where(ClassSchedule.teacher_id == teacher_id)
        .options(selectinload(ClassSchedule.gym_class))
    )

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# --------------------------------------------------------------------------- #
# Clases impartidas por el profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/classes/public", response_model=list[schemas.ClassSchedulePublic])
async def read_teacher_classes_public(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
):
    """Lista clases impartidas por el profesor (público)."""
    schedules = await crud.class_schedule.get_multi_filtered(db, teacher_id=teacher_id)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios del profesor (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/schedule", response_model=list[schemas.ClassSchedule])
async def read_teacher_schedule(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
    current_user: User = Depends(require_admin_or_teacher),
):
    """Lista horarios del profesor (operativo)."""
    stmt = (
        select(ClassSchedule)
        .where(ClassSchedule.teacher_id == teacher_id)
        .options(selectinload(ClassSchedule.gym_class))
    )

    res = await db.execute(stmt)
    return res.scalars().unique().all()


# --------------------------------------------------------------------------- #
# Horarios del profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/schedule/public", response_model=list[schemas.ClassSchedulePublic])
async def read_teacher_schedule_public(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
):
    """Lista horarios del profesor (público)."""
    schedules = await crud.class_schedule.get_multi_filtered(db, teacher_id=teacher_id)
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Próxima sesión del profesor
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/next-session", response_model=schemas.NextSessionInfo | None)
async def read_teacher_next_session(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
):
    """Devuelve la próxima sesión futura impartida por el profesor."""
    schedules = await crud.class_schedule.get_multi_filtered(
        db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    next_sessions = [get_next_session(s) for s in schedules]
    next_sessions = [ns for ns in next_sessions if ns is not None]

    if not next_sessions:
        return None

    return min(next_sessions, key=lambda ns: ns.starts_at)


# --------------------------------------------------------------------------- #
# Sesiones impartidas por el profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/sessions/public", response_model=list[schemas.ClassSessionInResponse])
async def read_teacher_sessions_public(
    *,
    db: AsyncSession = Depends(get_async_session),
    teacher_id: UUID,
):
    """Lista sesiones impartidas por el profesor (público)."""
    sessions = await crud.class_session.get_multi_filtered(
        db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    return [
        to_class_session_response(update_session_availability(s))
        for s in sessions
    ]

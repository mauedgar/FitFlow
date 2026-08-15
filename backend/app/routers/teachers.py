"""Router Teacher (Sprint 6-7).

---------------------------------
• CRUD de perfiles de profesores.
• Endpoints públicos y operativos.
• Integración con horarios y sesiones.
• Lógica centralizada en services.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import (
    require_admin,
    require_admin_or_teacher,
    require_admin_teacher_or_self,
)
from app.core.enums import UserRole
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_class_session import class_session
from app.crud.crud_teacher import teacher
from app.crud.crud_user import user as user_crud
from app.db.models.teacher import Teacher
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.class_schedule import (
    ClassSchedulePublic,
    ClassScheduleWithRelations,
    NextSessionInfo,
)
from app.schemas.class_session import ClassSessionInResponse
from app.schemas.teacher import (
    TeacherCreate,
    TeacherPublic,
    TeacherUpdate,
    TeacherWithRelations,
)
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

router = APIRouter(prefix="/teachers", tags=["teachers"])


# --------------------------------------------------------------------------- #
# Crear Teacher para un User existente
# --------------------------------------------------------------------------- #
@router.post("/{user_id}", response_model=TeacherWithRelations, status_code=status.HTTP_201_CREATED)
async def create_teacher_for_user(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: UUID,
    teacher_in: TeacherCreate,
    current_user: Annotated[User, Depends(require_admin)],  # noqa: ARG001
) -> TeacherWithRelations:
    """Crea un perfil de profesor asociado a un usuario existente.

    Reglas:
        • Solo administradores pueden crear perfiles de profesor.
        • El usuario debe existir.
        • El usuario no debe tener ya un `person_profile`.
        • El usuario debe tener rol `teacher`.
    """
    user = await user_crud.get(db=db, obj_id=user_id)
    if not user:
        raise HTTPException(404, f"El usuario {user_id} no existe.")

    if user.person_profile:
        raise HTTPException(400, "El usuario ya tiene un perfil asociado.")

    if user.role != UserRole.teacher: # pyright: ignore[reportGeneralTypeIssues]
        raise HTTPException(400, f"El usuario no tiene rol '{UserRole.teacher}'.")

    teacher_ = await teacher.create_with_user(db=db, obj_in=teacher_in, user=user)
    return TeacherWithRelations.model_validate(teacher_)


@router.get("/public", response_model=list[TeacherPublic])
async def read_public_teachers_first(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[TeacherPublic]:
    """Register the static public path before `/{teacher_id}`."""
    teachers = await teacher.get_multi(db=db)
    return [to_teacher_public(item) for item in teachers]


# --------------------------------------------------------------------------- #
# Listar Teachers (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[TeacherWithRelations])
async def read_teachers(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(require_admin_or_teacher)],  # noqa: ARG001
) -> list[TeacherWithRelations]:
    """Lista profesores en versión operativa (privada).

    Incluye:
        • Datos completos del profesor.
        • Horarios asociados (`class_schedules`) mediante `selectinload`.
    Usado en:
        • Panel administrativo.
        • Vistas internas de gestión de profesores.
    """
    teachers = await teacher.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        options=[selectinload(Teacher.class_schedules)], # pyright: ignore[reportArgumentType]
    )

    return [TeacherWithRelations.model_validate(t) for t in teachers]


# --------------------------------------------------------------------------- #
# Listar Teachers (público)
# --------------------------------------------------------------------------- #
async def read_public_teachers(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[TeacherPublic]:
    """Lista profesores en versión pública.

    Incluye:
        • Nombre, bio y foto de perfil.
        • NO incluye datos sensibles (cuil, documentos).
    Usado en:
        • Listados públicos del frontend.
        • Selección de profesor en la agenda.
    """
    teachers = await teacher.get_multi(db=db)
    return [to_teacher_public(t) for t in teachers]


# --------------------------------------------------------------------------- #
# Obtener Teacher por ID (privado)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}", response_model=TeacherWithRelations)
async def read_teacher_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
    current_user: Annotated[User, Depends(require_admin_teacher_or_self)],  # noqa: ARG001
) -> TeacherWithRelations:
    """Obtiene el perfil privado de un profesor por ID.

    Incluye:
        • Datos completos del profesor.
        • Horarios asociados (`class_schedules`).
    Reglas:
        • Solo admin, el propio profesor o roles autorizados pueden acceder.
    """
    teacher_ = await teacher.get(
        db=db,
        obj_id=teacher_id,
        include_relations=True,
    )
    if not teacher_:
        raise HTTPException(404, "Profesor no encontrado.")

    return TeacherWithRelations.model_validate(teacher_)


# --------------------------------------------------------------------------- #
# Obtener Teacher por ID (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/public", response_model=TeacherPublic)
async def read_teacher_public_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
) -> TeacherPublic:
    """Obtiene el perfil público de un profesor por ID.

    Incluye:
        • Nombre, bio y foto de perfil.
        • NO incluye datos sensibles.
    Usado en:
        • Fichas públicas de profesor en el frontend.
    """
    teacher_ = await teacher.get(db=db, obj_id=teacher_id)
    if not teacher_:
        raise HTTPException(404, "Profesor no encontrado.")

    return to_teacher_public(teacher_)


# --------------------------------------------------------------------------- #
# Actualizar Teacher
# --------------------------------------------------------------------------- #
@router.put("/{teacher_id}", response_model=TeacherWithRelations)
async def update_teacher(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
    teacher_in: TeacherUpdate,
    current_user: Annotated[User, Depends(require_admin_teacher_or_self)],  # noqa: ARG001
) -> TeacherWithRelations:
    """Actualiza el perfil privado de un profesor.

    Permite:
        • Modificar bio, cuil y datos personales heredados de Person.
    Reglas:
        • Solo admin o el propio profesor pueden actualizar su perfil.
    """
    teacher_ = await teacher.get(db=db, obj_id=teacher_id)
    if not teacher_:
        raise HTTPException(404, "Profesor no encontrado.")

    updated = await teacher.update(db=db, db_obj=teacher_, obj_in=teacher_in)
    return TeacherWithRelations.model_validate(updated)


# --------------------------------------------------------------------------- #
# Eliminar Teacher
# --------------------------------------------------------------------------- #
@router.delete("/{teacher_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_teacher(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],  # noqa: ARG001
) -> dict[str, str]:
    """Elimina un perfil de profesor.

    Reglas:
        • Solo administradores pueden eliminar profesores.
        • Si el profesor no existe, devuelve 404.
    Efecto:
        • Marca el registro como eliminado según tu estrategia de CRUD.
    """
    teacher_ = await teacher.get(db=db, obj_id=teacher_id)
    if not teacher_:
        raise HTTPException(404, "Profesor no encontrado.")

    await teacher.remove(db=db, db_obj=teacher_)
    return {"message": "Profesor eliminado exitosamente."}


# --------------------------------------------------------------------------- #
# Clases impartidas por el profesor (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/classes", response_model=list[ClassScheduleWithRelations])
async def read_teacher_classes(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
    current_user: Annotated[User, Depends(require_admin_or_teacher)],  # noqa: ARG001
) -> list[ClassScheduleWithRelations]:
    """Lista las clases/horarios impartidos por un profesor (operativo).

    Incluye:
        • Horarios (`ClassSchedule`) con relaciones cargadas.
    Usado en:
        • Panel interno para ver qué dicta cada profesor.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    return [ClassScheduleWithRelations.model_validate(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Clases impartidas por el profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/classes/public", response_model=list[ClassSchedulePublic])
async def read_teacher_classes_public(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
) -> list[ClassSchedulePublic]:
    """Lista las clases impartidas por un profesor en versión pública.

    Incluye:
        • Horarios públicos (`ClassSchedulePublic`).
    Usado en:
        • Frontend para mostrar la oferta de un profesor.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
    )
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios del profesor (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/schedule", response_model=list[ClassScheduleWithRelations])
async def read_teacher_schedule(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
    current_user: Annotated[User, Depends(require_admin_or_teacher)],  # noqa: ARG001
) -> list[ClassScheduleWithRelations]:
    """Lista el horario operativo completo de un profesor.

    Incluye:
        • Todos los `ClassSchedule` asociados al profesor.
    Usado en:
        • Vistas internas de planificación y agenda del profesor.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    return [ClassScheduleWithRelations.model_validate(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios del profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/schedule/public", response_model=list[ClassSchedulePublic])
async def read_teacher_schedule_public(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
) -> list[ClassSchedulePublic]:
    """Lista el horario público de un profesor.

    Incluye:
        • Horarios visibles para clientes y frontend.
    Usado en:
        • Agenda pública y selección de clases por profesor.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
    )
    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Próxima sesión del profesor
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/next-session", response_model=NextSessionInfo | None)
async def read_teacher_next_session(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
) -> NextSessionInfo | None:
    """Devuelve la próxima sesión futura impartida por el profesor.

    Lógica:
        • Obtiene todos los horarios del profesor.
        • Calcula la próxima sesión futura (`get_next_session`).
        • Devuelve la sesión más cercana en el tiempo.
    Si no hay sesiones futuras:
        • Devuelve `None`.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    next_sessions = [
        ns for s in schedules
        if (ns := get_next_session(s)) is not None
    ]

    if not next_sessions:
        return None

    return min(next_sessions, key=lambda ns: ns.starts_at)


# --------------------------------------------------------------------------- #
# Sesiones impartidas por el profesor (público)
# --------------------------------------------------------------------------- #
@router.get("/{teacher_id}/sessions/public", response_model=list[ClassSessionInResponse])
async def read_teacher_sessions_public(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    teacher_id: UUID,
) -> list[ClassSessionInResponse]:
    """Lista las sesiones impartidas por el profesor en versión pública.

    Incluye:
        • Sesiones (`ClassSession`) con disponibilidad actualizada.
        • Transformación a esquema de respuesta (`ClassSessionInResponse`).
    Usado en:
        • Frontend para ver todas las sesiones de un profesor.
    """
    sessions = await class_session.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
        include_relations=True,
    )

    return [
        to_class_session_response(update_session_availability(s))
        for s in sessions
    ]

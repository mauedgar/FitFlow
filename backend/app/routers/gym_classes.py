"""Router GymClass (Sprint 6-7).
---------------------------------
• CRUD del catálogo de clases.
• Filtros operativos avanzados.
• Versiones públicas y operativas.
• Integración con horarios y sesiones.
• Lógica centralizada en services.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_gym_class import gym_class
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.class_schedule import ClassSchedulePublic, NextSessionInfo
from app.schemas.gym_class import (
    GymClassCreate,
    GymClassPublic,
    GymClassUpdate,
    GymClassWithRelations,
)
from app.services import gym_class_service
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)
from app.services.gym_class_service import (
    to_gym_class_public,
)

router = APIRouter(prefix="/gym-classes", tags=["gym-classes"])


# --------------------------------------------------------------------------- #
# Crear GymClass
# --------------------------------------------------------------------------- #
@router.post("/", response_model=GymClassWithRelations, status_code=status.HTTP_201_CREATED)
async def create_gym_class(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    class_in: GymClassCreate,
) -> GymClassWithRelations:
    """Crea una nueva clase en el catálogo.

    Incluye:
        • Nombre, descripción, dificultad, duración, tipo de actividad.
        • Capacidad por defecto e imagen opcional.

    Usado en:
        • Panel administrativo para gestionar el catálogo.
    """
    gym_classs = await gym_class.create(db=db, obj_in=class_in)
    return GymClassWithRelations.model_validate(gym_classs)


@router.get("/public", response_model=list[GymClassPublic])
async def list_public_gym_classes_first(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GymClassPublic]:
    """Register the static public path before `/{class_id}`."""
    classes = await gym_class.get_multi(db=db)
    return [to_gym_class_public(item) for item in classes]


# --------------------------------------------------------------------------- #
# Listar GymClasses (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[GymClassWithRelations])
async def list_gym_classes(  # noqa: PLR0913
    *,
    skip: Annotated[int, Query(ge=0)]=0,
    limit: Annotated[int, Query(ge=1, le=200)]=50,
    difficulty: Annotated[str | None, Query()] = None,
    activity_type: Annotated[str | None, Query()] = None,
    active: Annotated[bool | None, Query()]=True,
    search: Annotated[str | None, Query()] = None,
    teacher_id: Annotated[UUID | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    include_schedules: Annotated[bool, Query()] = False,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GymClassWithRelations]:
    """Lista clases del catálogo con filtros operativos.

    Filtros disponibles:
        • dificultad
        • tipo de actividad
        • estado activo/inactivo
        • búsqueda por nombre
        • profesor asignado
        • rango de fechas

    Si `include_schedules=True`, se incluyen los horarios asociados.
    """
    classes = await gym_class.get_multi_filtered(
        db=db,
        skip=skip,
        limit=limit,
        difficulty=difficulty,
        activity_type=activity_type,
        active=active,
        search=search,
        teacher_id=teacher_id,
        date_from=date_from,
        date_to=date_to,
    )

    if not include_schedules:
        return [GymClassWithRelations.model_validate(c) for c in classes]

    ids = [c.id for c in classes]
    classes_with_sched = await gym_class.get_multi(
        db=db,
        filters={"id": ids},
        options=[
            gym_class.model.class_schedules.property.lazyload,
        ],
    )

    classes_map = {c.id: c for c in classes_with_sched}
    return [GymClassWithRelations.model_validate(classes_map[i]) for i in ids]
# --------------------------------------------------------------------------- #
# Obtener GymClass por ID (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{class_id}", response_model=GymClassWithRelations)
async def read_gym_class(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    _: Annotated[User, Depends(require_admin)],
) -> GymClassWithRelations:
    """Obtiene una clase del catálogo por ID.

    Incluye:
        • Datos completos de la clase.
        • Horarios asociados (si `include_schedules=True` en el CRUD).
    """
    gym_classs = await gym_class.get(
        db=db,
        obj_id=class_id,
        include_schedules=True,
    )
    if not gym_classs:
        raise HTTPException(404, "Clase no encontrada")

    return GymClassWithRelations.model_validate(gym_classs)


# --------------------------------------------------------------------------- #
# Actualizar GymClass
# --------------------------------------------------------------------------- #
@router.put("/{class_id}", response_model=GymClassWithRelations)
async def update_gym_class(
    *,
    class_id: UUID,
    class_in: GymClassUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> GymClassWithRelations:
    """Actualiza una clase del catálogo.

    Permite modificar:
        • nombre
        • descripción
        • dificultad
        • duración
        • tipo de actividad
        • capacidad por defecto
        • imagen
    """
    gym_classs = await gym_class.get(db=db, obj_id=class_id)
    if not gym_classs:
        raise HTTPException(404, "Clase no encontrada")

    updated = await gym_class.update(db=db, db_obj=gym_classs, obj_in=class_in)
    return GymClassWithRelations.model_validate(updated)


# --------------------------------------------------------------------------- #
# Eliminar GymClass (soft delete)
# --------------------------------------------------------------------------- #
@router.delete("/{class_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_gym_class(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Elimina una clase del catálogo (soft delete).

    Reglas:
        • Si la clase no existe → 404.
        • Se marca como eliminada según tu estrategia de SoftDeleteMixin.
    """
    gym_classs = await gym_class.get(db=db, obj_id=class_id)
    if not gym_classs:
        raise HTTPException(404, "Clase no encontrada")

    await gym_class.remove(db=db, db_obj=gym_classs) # pyright: ignore[reportArgumentType]
    return {"detail": "GymClass desactivada"}


# --------------------------------------------------------------------------- #
# Listado público de clases
# --------------------------------------------------------------------------- #
async def list_public_gym_classes(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GymClassPublic]:
    """Lista pública del catálogo de clases.

    Incluye:
        • nombre
        • descripción
        • dificultad
        • imagen
    """
    classes = await gym_class.get_multi(db=db)
    return [to_gym_class_public(c) for c in classes]
# --------------------------------------------------------------------------- #
# Clase pública por ID
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/public", response_model=GymClassPublic)
async def read_public_gym_class(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> GymClassPublic:
    """Devuelve una clase. Con sus datos sin schedules."""
    gym_classs = await gym_class.get(db=db, obj_id=class_id,include_schedules=False)
    if not gym_classs:
            raise HTTPException(404, "Clase no encontrada")
    return to_gym_class_public(gym_classs)

# Próxima sesión de una clase
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/next-session", response_model=NextSessionInfo | None)
async def read_class_next_session(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> NextSessionInfo | None:
    """Devuelve la próxima sesión futura de una clase.

    Lógica:
        • Obtiene todos los horarios de la clase.
        • Calcula la próxima sesión futura (`get_next_session`).
        • Devuelve la sesión más cercana en el tiempo.
    """
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        gym_class_id=class_id,
        include_relations=True,
    )

    next_sessions = [
        ns for s in schedules
        if (ns := get_next_session(s)) is not None
    ]

    if not next_sessions:
        return None

    return min(next_sessions, key=lambda ns: ns.starts_at)
    """Obtiene una clase en versión pública.

    Incluye:
        • datos públicos de la clase
        • horarios públicos asociados
    """
    gym_classs = await gym_class.get(db=db, obj_id=class_id, include_schedules=True)
    if not gym_classs:
        raise HTTPException(404, "Clase no encontrada")

    return to_gym_class_public(gym_classs)


# --------------------------------------------------------------------------- #
# Horarios públicos de una clase
# --------------------------------------------------------------------------- #
@router.get("/{class_id}/schedules/public", response_model=list[ClassSchedulePublic])
async def read_public_class_schedules(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSchedulePublic]:
    """Lista horarios públicos de una clase."""
    schedules = await class_schedule.get_multi_filtered(
        db=db,
        gym_class_id=class_id,
    )
    return [to_class_schedule_public(s) for s in schedules]


#


# --------------------------------------------------------------------------- #
# Clases públicas impartidas por un profesor
# --------------------------------------------------------------------------- #
@router.get("/teacher/{teacher_id}/public", response_model=list[GymClassPublic])
async def read_public_classes_by_teacher(
    *,
    teacher_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GymClassPublic]:
    """Lista clases públicas impartidas por un profesor."""
    classes = await gym_class.get_multi_filtered(
        db=db,
        teacher_id=teacher_id,
    )
    return [to_gym_class_public(c) for c in classes]



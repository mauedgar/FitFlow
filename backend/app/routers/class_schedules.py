# app/api/routes/class_schedules.py
"""Router ClassSchedule (Sprint 6-7).

---------------------------------
• CRUD de horarios recurrentes.
• Endpoints públicos y operativos.
• Lógica centralizada en services.
• Respuestas optimizadas para frontend.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.core.deps import (
    require_admin,
    require_admin_or_front_desk,
)
from app.crud.crud_class_schedule import class_schedule as class_schedule_crud
from app.crud.crud_gym_class import gym_class as gym_class_crud
from app.crud.crud_teacher import teacher as teacher_crud
from app.db.session import get_async_session
from app.schemas.class_schedule import (
    ClassSchedule,
    ClassScheduleCreate,
    ClassSchedulePublic,
    ClassScheduleUpdate,
    NextSessionInfo,
)
from app.schemas.user import UserPublic  # noqa: TC001
from app.services import errors as svc_errors
from app.services.class_schedule_service import (
    generate_sessions_for_schedule,
    get_schedule_next_session,
    to_class_schedule_public,
)

#ruff :noqa: TRY301,B904
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/class-schedules", tags=["class-schedules"])


# --------------------------------------------------------------------------- #
# Crear horario
# --------------------------------------------------------------------------- #
@router.post("/", response_model=ClassSchedule, status_code=status.HTTP_201_CREATED)
async def create_class_schedule(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    schedule_in: ClassScheduleCreate,
    current_user: Annotated[UserPublic, Depends(require_admin_or_front_desk)],
) -> ClassSchedule:
    """Crea un horario recurrente para una clase.

    Valida existencia de gym_class y teacher, crea el schedule y genera sesiones
    por defecto (próxima semana) mediante el service.
    """
    try:
        gym_class = await gym_class_crud.get(db=db, obj_id=schedule_in.gym_class_id)
        if not gym_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GymClass {schedule_in.gym_class_id} no existe.")

        teacher = await teacher_crud.get(db=db, obj_id=schedule_in.teacher_id)
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Teacher {schedule_in.teacher_id} no existe.")

        schedule = await class_schedule_crud.create(db=db, obj_in=schedule_in, created_by=getattr(current_user, "id", None))
    except svc_errors.BusinessValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError as err:
        logger.debug("IntegrityError creando ClassSchedule: %s", err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Violación de integridad en la base de datos.") from err
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia creando ClassSchedule")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de persistencia en la base de datos.") from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Error inesperado creando ClassSchedule")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creando ClassSchedule") from err

    # Generar sesiones por defecto (próxima semana). No romper la creación si falla.
    try:
        window_start = datetime.date.today()
        window_end = window_start + timedelta(days=7)
        await generate_sessions_for_schedule(str(schedule.id), window_start, window_end, current_user, db=db)
    except Exception:
        logger.exception("Fallo generando sesiones automáticas para schedule %s", getattr(schedule, "id", "<unknown>"))
        # No re-lanzamos para no romper la creación; registrar para monitoreo.

    return ClassSchedule.model_validate(schedule)


# --------------------------------------------------------------------------- #
# Listar horarios (operativo)
# --------------------------------------------------------------------------- #
@router.get("/", response_model=list[ClassSchedule])
async def read_class_schedules(  # noqa: PLR0913
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    gym_class_id: UUID | None = None,
    teacher_id: UUID | None = None,
    day_of_week: int | None = None,
    include_relations: Annotated[bool, Query()] = False,
) -> list[ClassSchedule]:
    """Lista horarios con filtros operativos."""
    try:
        schedules = await class_schedule_crud.get_multi_filtered(
            db=db,
            skip=skip,
            limit=limit,
            gym_class_id=gym_class_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            include_relations=include_relations,
        )
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia listando ClassSchedules")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando ClassSchedules") from err
    except Exception as err:
        logger.exception("Error inesperado listando ClassSchedules")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando ClassSchedules") from err

    return [ClassSchedule.model_validate(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Obtener horario por ID (operativo)
# --------------------------------------------------------------------------- #
@router.get("/{schedule_id}", response_model=ClassSchedule)
async def read_class_schedule_by_id(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    schedule_id: UUID,
) -> ClassSchedule:
    """Obtiene un horario por ID."""
    try:
        schedule = await class_schedule_crud.get(
            db=db,
            obj_id=schedule_id,
            include_relations=True,
        )
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ClassSchedule {schedule_id} no encontrado.")
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia obteniendo ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error obteniendo ClassSchedule") from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Error inesperado obteniendo ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error obteniendo ClassSchedule") from err

    return ClassSchedule.model_validate(schedule)


# --------------------------------------------------------------------------- #
# Actualizar horario
# --------------------------------------------------------------------------- #
@router.put("/{schedule_id}", response_model=ClassSchedule)
async def update_class_schedule(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    schedule_id: UUID,
    schedule_in: ClassScheduleUpdate,
    current_user: Annotated[UserPublic, Depends(require_admin_or_front_desk)],
    regenerate: Annotated[bool, Query(description="Si true, regenera sesiones en la ventana por defecto")] = False,
) -> ClassSchedule:
    """Actualiza un horario."""
    try:
        schedule = await class_schedule_crud.get(db=db, obj_id=schedule_id)
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado.")

        updated = await class_schedule_crud.update(
            db=db,
            db_obj=schedule,
            obj_in=schedule_in,
        )
    except svc_errors.BusinessValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia actualizando ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error actualizando ClassSchedule") from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Error inesperado actualizando ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error actualizando ClassSchedule") from err

    if regenerate:
        try:
            window_start = datetime.date.today()
            window_end = window_start + timedelta(days=7)
            await generate_sessions_for_schedule(str(schedule_id), window_start, window_end, current_user, db=db)
        except svc_errors.BusinessValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        except Exception as err:
            logger.exception("Error regenerando sesiones para ClassSchedule %s", schedule_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error regenerando sesiones") from err

    return ClassSchedule.model_validate(updated)


# --------------------------------------------------------------------------- #
# Eliminar horario
# --------------------------------------------------------------------------- #
@router.delete("/{schedule_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_class_schedule(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    schedule_id: UUID,
    current_user: Annotated[UserPublic, Depends(require_admin)],  # noqa: ARG001
) -> dict[str, str]:
    """Elimina un horario."""
    try:
        schedule = await class_schedule_crud.get(db=db, obj_id=schedule_id)
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado.")

        await class_schedule_crud.remove(db=db, obj_id=schedule_id)
    except svc_errors.NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia eliminando ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error eliminando ClassSchedule") from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Error inesperado eliminando ClassSchedule %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error eliminando ClassSchedule") from err

    return {"message": "Horario eliminado exitosamente."}


# --------------------------------------------------------------------------- #
# Horarios públicos
# --------------------------------------------------------------------------- #
@router.get("/public", response_model=list[ClassSchedulePublic])
async def read_public_schedules(
    *,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ClassSchedulePublic]:
    """Lista horarios públicos."""
    try:
        schedules = await class_schedule_crud.get_multi_filtered(
            db=db,
            skip=skip,
            limit=limit,
            active=True,
            include_relations=False,
        )
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia listando horarios públicos")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err
    except Exception as err:
        logger.exception("Error inesperado listando horarios públicos")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err

    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios públicos por clase
# --------------------------------------------------------------------------- #
@router.get("/class/{class_id}/public", response_model=list[ClassSchedulePublic])
async def read_public_schedules_by_class(
    *,
    class_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSchedulePublic]:
    """Lista horarios públicos de una clase."""
    try:
        schedules = await class_schedule_crud.get_multi_filtered(
            db=db,
            gym_class_id=class_id,
            active=True,
        )
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia listando horarios públicos por clase %s", class_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err
    except Exception as err:
        logger.exception("Error inesperado listando horarios públicos por clase %s", class_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err

    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Horarios públicos por profesor
# --------------------------------------------------------------------------- #
@router.get("/teacher/{teacher_id}/public", response_model=list[ClassSchedulePublic])
async def read_public_schedules_by_teacher(
    *,
    teacher_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[ClassSchedulePublic]:
    """Lista horarios públicos de un profesor."""
    try:
        schedules = await class_schedule_crud.get_multi_filtered(
            db=db,
            teacher_id=teacher_id,
            active=True,
        )
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia listando horarios públicos por teacher %s", teacher_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err
    except Exception as err:
        logger.exception("Error inesperado listando horarios públicos por teacher %s", teacher_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error listando horarios públicos") from err

    return [to_class_schedule_public(s) for s in schedules]


# --------------------------------------------------------------------------- #
# Próxima sesión de un horario
# --------------------------------------------------------------------------- #
@router.get("/{schedule_id}/next-session", response_model=NextSessionInfo | None)
async def read_next_session(
    *,
    schedule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> NextSessionInfo | None:
    """Devuelve la próxima sesión futura de un horario."""
    try:
        schedule = await class_schedule_crud.get(
            db=db,
            obj_id=schedule_id,
            include_relations=True,
        )
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado.")

        return get_schedule_next_session(schedule)
    except SQLAlchemyError as err:
        logger.exception("Error de persistencia obteniendo próxima sesión para %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error obteniendo próxima sesión") from err
    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Error inesperado obteniendo próxima sesión para %s", schedule_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error obteniendo próxima sesión") from err

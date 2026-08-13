"""Servicios para Teacher.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con horarios y próximas sesiones.
• Validaciones de negocio.
• Métricas operativas.
• Helpers para frontend y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.schemas.teacher import (
    TeacherPublic,
    TeacherWithMetrics,
    TeacherWithNextSession,
    TeacherWithSchedules,
)
from app.services.class_schedule_service import (
    get_schedule_next_session,
    to_class_schedule_public,
)

if TYPE_CHECKING:
    from app.db.models import Teacher


# --------------------------------------------------------------------------- #
# 1. Transformación automática: Teacher → TeacherPublic
# --------------------------------------------------------------------------- #

def to_teacher_public(teacher: Teacher) -> TeacherPublic:
    """Transforma un modelo ORM Teacher en un esquema público."""
    return TeacherPublic(
        id=teacher.id, # pyright: ignore[reportArgumentType]
        first_name=teacher.first_name, # pyright: ignore[reportArgumentType]
        last_name=teacher.last_name, # pyright: ignore[reportArgumentType]
        full_name=teacher.full_name,
        bio=teacher.bio, # pyright: ignore[reportArgumentType]
        profile_image_url=teacher.profile_image_url, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Validaciones de negocio
# --------------------------------------------------------------------------- #

def validate_teacher_active(teacher: Teacher) -> None:
    """Valida que el profesor esté activo y tenga horarios asignados."""
    if not teacher.active: # pyright: ignore[reportGeneralTypeIssues]
        msg = "El profesor no está activo."
        raise ValueError(msg)
    if not teacher.class_schedules:
        msg_0 = "El profesor no tiene horarios asignados."
        raise ValueError(msg_0)


# --------------------------------------------------------------------------- #
# 3. Estado emergente del profesor
# --------------------------------------------------------------------------- #

def has_sessions_today(teacher: Teacher) -> bool:
    """Indica si el profesor tiene sesiones hoy."""
    today = datetime.now(tz=timezone.utc).date()
    return any(
        s.starts_at.date() == today
        for sch in teacher.class_schedules
        for s in sch.class_sessions
    )


def has_future_sessions(teacher: Teacher) -> bool:
    """Indica si el profesor tiene sesiones futuras."""
    now = datetime.now(tz=timezone.utc)
    return any(
        s.starts_at > now
        for sch in teacher.class_schedules
        for s in sch.class_sessions
    )


# --------------------------------------------------------------------------- #
# 4. Métricas del profesor
# --------------------------------------------------------------------------- #

def get_teacher_total_classes(teacher: Teacher) -> int:
    """Devuelve la cantidad total de clases que dicta el profesor."""
    return len(teacher.class_schedules)


def get_teacher_future_sessions_count(teacher: Teacher) -> int:
    """Devuelve la cantidad de sesiones futuras del profesor."""
    now = datetime.now(tz=timezone.utc)
    return sum(
        1 for sch in teacher.class_schedules for s in sch.class_sessions if s.starts_at > now # pyright: ignore[reportGeneralTypeIssues]
    )


def get_teacher_average_occupancy(teacher: Teacher) -> float:
    """Calcula la ocupación promedio de las sesiones del profesor."""
    sessions = [
        s for sch in teacher.class_schedules for s in sch.class_sessions
    ]
    if not sessions:
        return 0.0

    total = sum(s.current_bookings_count for s in sessions)  # type: ignore[attr-defined]
    capacity = sum(s.capacity_snapshot for s in sessions)
    return total / capacity if capacity > 0 else 0.0 # pyright: ignore[reportGeneralTypeIssues, reportReturnType]


# --------------------------------------------------------------------------- #
# 5. Extender Teacher con horarios públicos
# --------------------------------------------------------------------------- #

def to_teacher_with_schedules(teacher: Teacher) -> TeacherWithSchedules:
    """Extiende el profesor con sus horarios públicos."""
    schedules = [to_class_schedule_public(s) for s in teacher.class_schedules]

    return TeacherWithSchedules(
        **to_teacher_public(teacher).model_dump(),
        schedules=schedules,
    )


# --------------------------------------------------------------------------- #
# 6. Extender Teacher con próxima sesión futura
# --------------------------------------------------------------------------- #

def to_teacher_with_next_session(teacher: Teacher) -> TeacherWithNextSession:
    """Extiende el profesor con su próxima sesión futura."""
    next_sessions = [
        get_schedule_next_session(s)
        for s in teacher.class_schedules
    ]

    next_upcoming = min(
        [ns for ns in next_sessions if ns is not None],
        key=lambda ns: ns.starts_at,
        default=None,
    )

    return TeacherWithNextSession(
        **to_teacher_public(teacher).model_dump(),
        next_session=next_upcoming,
    )


# --------------------------------------------------------------------------- #
# 7. Extender Teacher con métricas operativas
# --------------------------------------------------------------------------- #

def to_teacher_with_metrics(teacher: Teacher) -> TeacherWithMetrics:
    """Extiende el profesor con métricas operativas para dashboards."""
    return TeacherWithMetrics(
        **to_teacher_public(teacher).model_dump(),
        total_classes=get_teacher_total_classes(teacher),
        future_sessions=get_teacher_future_sessions_count(teacher),
        average_occupancy=get_teacher_average_occupancy(teacher),
    )

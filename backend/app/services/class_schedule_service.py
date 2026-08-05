"""Servicios para ClassSchedule.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Validaciones de negocio.
• Estado emergente del horario.
• Métricas operativas.
• Sesiones del día y de la semana.
• Próxima sesión futura.
• Helpers para front desk y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app import schemas

if TYPE_CHECKING:
    from app.models import ClassSchedule, ClassSession


# --------------------------------------------------------------------------- #
# 1. Transformación automática: ClassSchedule → ClassSchedulePublic
# --------------------------------------------------------------------------- #

def to_class_schedule_public(schedule: ClassSchedule) -> schemas.ClassSchedulePublic:
    """Transforma un modelo ORM ClassSchedule en un esquema público."""
    return schemas.ClassSchedulePublic(
        id=schedule.id,
        days_of_week=schedule.days_of_week,
        start_time=schedule.start_time,
        duration_minutes=schedule.duration_minutes,
        capacity=schedule.capacity,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher, # pyright: ignore[reportCallIssue]
        allowed_plan=schedule.allowed_plan, # pyright: ignore[reportCallIssue]
    )


# --------------------------------------------------------------------------- #
# 2. Validaciones de negocio del horario
# --------------------------------------------------------------------------- #

def validate_schedule_active(schedule: ClassSchedule) -> None:
    """Valida que el horario esté dentro de su rango de fechas."""
    now = datetime.now(tz=timezone.utc)

    if schedule.start_date and now < schedule.start_date: # pyright: ignore[reportGeneralTypeIssues]
        msg = "El horario aún no está activo."
        raise ValueError(msg)

    if schedule.end_date and now > schedule.end_date: # pyright: ignore[reportGeneralTypeIssues]
        msg_0 = "El horario ya no está activo."
        raise ValueError(msg_0)


def validate_schedule_integrity(schedule: ClassSchedule) -> None:
    """Valida que el horario tenga clase, profesor y capacidad válida."""
    if schedule.gym_class is None:
        msg = "El horario no tiene clase asignada."
        raise ValueError(msg)

    if schedule.teacher is None:
        msg_0 = "El horario no tiene profesor asignado."
        raise ValueError(msg_0)

    if schedule.capacity <= 0: # pyright: ignore[reportGeneralTypeIssues]
        msg_1 = "El horario tiene una capacidad inválida."
        raise ValueError(msg_1)


# --------------------------------------------------------------------------- #
# 3. Estado emergente del horario
# --------------------------------------------------------------------------- #

def has_sessions_today(schedule: ClassSchedule) -> bool:
    """Indica si el horario tiene sesiones hoy."""
    today = datetime.now(tz=timezone.utc).date()
    return any(s.starts_at.date() == today for s in schedule.class_sessions)


def has_future_sessions(schedule: ClassSchedule) -> bool:
    """Indica si el horario tiene sesiones futuras."""
    now = datetime.now(tz=timezone.utc)
    return any(s.starts_at > now for s in schedule.class_sessions)


def get_sessions_today(schedule: ClassSchedule) -> list[ClassSession]:
    """Devuelve las sesiones del día para este horario."""
    today = datetime.now(tz=timezone.utc).date()
    return [s for s in schedule.class_sessions if s.starts_at.date() == today]


def get_sessions_this_week(schedule: ClassSchedule) -> list[ClassSession]:
    """Devuelve las sesiones de los próximos 7 días."""
    now = datetime.now(tz=timezone.utc)
    limit = now + timedelta(days=7)
    return [s for s in schedule.class_sessions if now < s.starts_at <= limit] # pyright: ignore[reportGeneralTypeIssues]


# --------------------------------------------------------------------------- #
# 4. Métricas del horario
# --------------------------------------------------------------------------- #

def get_schedule_occupancy(schedule: ClassSchedule) -> float:
    """Devuelve la ocupación promedio del horario."""
    sessions = schedule.class_sessions
    if not sessions:
        return 0.0

    total = sum(s.current_bookings_count for s in sessions)  # type: ignore[attr-defined]
    capacity = sum(s.capacity_snapshot for s in sessions)

    if capacity == 0: # pyright: ignore[reportGeneralTypeIssues]
        return 0.0

    return total / capacity # pyright: ignore[reportReturnType]


def get_schedule_next_session(schedule: ClassSchedule) -> schemas.NextSessionInfo | None:
    """Devuelve la próxima sesión futura del horario."""
    now = datetime.now(tz=timezone.utc)

    future_sessions = [
        s for s in schedule.class_sessions
        if s.starts_at > now # pyright: ignore[reportGeneralTypeIssues]
    ]

    if not future_sessions:
        return None

    next_session = min(future_sessions, key=lambda s: s.starts_at)

    return schemas.NextSessionInfo(
        starts_at=next_session.starts_at, # pyright: ignore[reportArgumentType]
        available_spots=next_session.available_spots,  # type: ignore[attr-defined]
    )


# --------------------------------------------------------------------------- #
# 5. Transformación completa con próxima sesión
# --------------------------------------------------------------------------- #

def to_class_schedule_with_next_session(
    schedule: ClassSchedule,
) -> schemas.ClassScheduleWithNextSession:
    """Extiende el esquema completo de ClassSchedule con la próxima sesión futura."""
    return schemas.ClassScheduleWithNextSession(
        id=schedule.id,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher, # pyright: ignore[reportCallIssue]
        days_of_week=schedule.days_of_week,
        start_time=schedule.start_time,
        duration_minutes=schedule.duration_minutes,
        capacity=schedule.capacity,
        start_date=schedule.start_date, # pyright: ignore[reportCallIssue]
        end_date=schedule.end_date, # pyright: ignore[reportCallIssue]
        allowed_plan=schedule.allowed_plan, # pyright: ignore[reportCallIssue]
        next_upcoming_session=get_schedule_next_session(schedule), # pyright: ignore[reportCallIssue]
    )

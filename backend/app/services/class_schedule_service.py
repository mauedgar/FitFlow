"""
Servicios para ClassSchedule (Sprint 6–7)
-----------------------------------------
Incluye:
• Transformaciones ORM → Schemas públicos.
• Cálculo de próxima sesión futura.
• Helpers operativos para front desk y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import ClassSchedule

# --------------------------------------------------------------------------- #
# 1. Transformación automática: ClassSchedule → ClassSchedulePublic
# --------------------------------------------------------------------------- #

def to_class_schedule_public(schedule: ClassSchedule) -> schemas.ClassSchedulePublic:
    """
    Transforma un modelo ORM ClassSchedule en un esquema público.
    Usado en:
        • TeacherPublic
        • listados públicos de horarios
        • front desk
    """
    return schemas.ClassSchedulePublic(
        id=schedule.id,
        days_of_week=schedule.days_of_week,
        start_time=schedule.start_time,
        duration_minutes=schedule.duration_minutes,
        capacity=schedule.capacity,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher,
        allowed_plan=schedule.allowed_plan,
    )


# --------------------------------------------------------------------------- #
# 2. Cálculo de próxima sesión futura
# --------------------------------------------------------------------------- #

def get_next_session(schedule: ClassSchedule) -> schemas.NextSessionInfo | None:
    """
    Devuelve la próxima sesión futura del horario.
    Si no hay sesiones futuras, devuelve None.
    """
    now = datetime.now(tz=timezone.utc)

    future_sessions = [
        s for s in schedule.class_sessions
        if s.starts_at > now
    ]

    if not future_sessions:
        return None

    next_session = min(future_sessions, key=lambda s: s.starts_at)

    return schemas.NextSessionInfo(
        starts_at=next_session.starts_at,
        available_spots=next_session.available_spots,
    )


# --------------------------------------------------------------------------- #
# 3. Transformación completa con próxima sesión
# --------------------------------------------------------------------------- #

def to_class_schedule_with_next_session(
    schedule: ClassSchedule,
) -> schemas.ClassScheduleWithNextSession:
    """
    Extiende el esquema completo de ClassSchedule con la próxima sesión futura.
    """
    return schemas.ClassScheduleWithNextSession(
        id=schedule.id,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher,
        days_of_week=schedule.days_of_week,
        start_time=schedule.start_time,
        duration_minutes=schedule.duration_minutes,
        capacity=schedule.capacity,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        allowed_plan=schedule.allowed_plan,
        next_upcoming_session=get_next_session(schedule),
    )

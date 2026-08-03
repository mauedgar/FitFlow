"""
Servicios para Teacher
======================

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con horarios y próximas sesiones.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from app import schemas
from app.models import Teacher
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)

# --------------------------------------------------------------------------- #
# 1. Transformación automática: Teacher → TeacherPublic
# --------------------------------------------------------------------------- #

def to_teacher_public(teacher: Teacher) -> schemas.TeacherPublic:
    return schemas.TeacherPublic(
        id=teacher.id,
        full_name=teacher.full_name,
        bio=teacher.bio,
        avatar_url=teacher.avatar_url,
    )


# --------------------------------------------------------------------------- #
# 2. Extender Teacher con horarios públicos
# --------------------------------------------------------------------------- #

def to_teacher_with_schedules(teacher: Teacher) -> schemas.TeacherWithSchedules:
    schedules = [
        to_class_schedule_public(s)
        for s in teacher.class_schedules
    ]

    return schemas.TeacherWithSchedules(
        **to_teacher_public(teacher).model_dump(),
        schedules=schedules,
    )


# --------------------------------------------------------------------------- #
# 3. Extender Teacher con próxima sesión futura
# --------------------------------------------------------------------------- #

def to_teacher_with_next_session(teacher: Teacher) -> schemas.TeacherWithNextSession:
    next_sessions = [
        get_next_session(s)
        for s in teacher.class_schedules
    ]

    next_upcoming = min(
        [ns for ns in next_sessions if ns is not None],
        key=lambda ns: ns.starts_at,
        default=None,
    )

    return schemas.TeacherWithNextSession(
        **to_teacher_public(teacher).model_dump(),
        next_upcoming_session=next_upcoming,
    )

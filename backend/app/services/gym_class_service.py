"""
Servicios para GymClass
=======================

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con horarios y próximas sesiones.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from app import schemas
from app.models import GymClass
from app.services.class_schedule_service import (
    get_next_session,
    to_class_schedule_public,
)

# --------------------------------------------------------------------------- #
# 1. Transformación automática: GymClass → GymClassPublic
# --------------------------------------------------------------------------- #

def to_gym_class_public(gym_class: GymClass) -> schemas.GymClassPublic:
    return schemas.GymClassPublic(
        id=gym_class.id,
        name=gym_class.name,
        description=gym_class.description,
        difficulty=gym_class.difficulty,
        image_url=gym_class.image_url,
    )


# --------------------------------------------------------------------------- #
# 2. Extender GymClass con horarios públicos
# --------------------------------------------------------------------------- #

def to_gym_class_with_schedules(gym_class: GymClass) -> schemas.GymClassWithSchedules:
    schedules = [
        to_class_schedule_public(s)
        for s in gym_class.class_schedules
    ]

    return schemas.GymClassWithSchedules(
        **to_gym_class_public(gym_class).model_dump(),
        schedules=schedules,
    )


# --------------------------------------------------------------------------- #
# 3. Extender GymClass con próxima sesión futura
# --------------------------------------------------------------------------- #

def to_gym_class_with_next_session(gym_class: GymClass) -> schemas.GymClassWithNextSession:
    next_sessions = [
        get_next_session(s)
        for s in gym_class.class_schedules
    ]

    next_upcoming = min(
        [ns for ns in next_sessions if ns is not None],
        key=lambda ns: ns.starts_at,
        default=None,
    )

    return schemas.GymClassWithNextSession(
        **to_gym_class_public(gym_class).model_dump(),
        next_upcoming_session=next_upcoming,
    )

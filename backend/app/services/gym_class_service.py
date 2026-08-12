"""Servicios para GymClass.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Extensiones con horarios públicos.
• Helpers operativos para frontend y dashboards.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.gym_class import GymClassPublic, GymClassWithSchedules
from app.services.class_schedule_service import to_class_schedule_public

if TYPE_CHECKING:
    from backend.app.db.models import GymClass


# --------------------------------------------------------------------------- #
# 1. Transformación automática: GymClass → GymClassPublic
# --------------------------------------------------------------------------- #

def to_gym_class_public(gym_class: GymClass) -> GymClassPublic:
    """Transforma un modelo ORM GymClass en su versión pública."""
    return GymClassPublic(
        id=gym_class.id,
        name=gym_class.name,
        description=gym_class.description,
        difficulty=gym_class.difficulty,
        image_url=gym_class.image_url,
    ) # pyright: ignore[reportCallIssue]


# --------------------------------------------------------------------------- #
# 2. Extender GymClass con horarios públicos
# --------------------------------------------------------------------------- #

def to_gym_class_with_schedules(gym_class: GymClass) -> GymClassWithSchedules:
    """Extiende GymClass con sus horarios públicos asociados."""
    schedules = [
        to_class_schedule_public(s)
        for s in gym_class.class_schedules
    ]

    return GymClassWithSchedules(
        **to_gym_class_public(gym_class).model_dump(),
        schedules=schedules,
    )

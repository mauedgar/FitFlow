"""Metadata completa de los modelos ORM activos de FitFlow."""

from app.db.base_class import Base
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Person,
    Teacher,
    User,
)

__all__ = [
    "Base",
    "Booking",
    "ClassSchedule",
    "ClassSession",
    "Client",
    "GymClass",
    "Membership",
    "Person",
    "Teacher",
    "User",
]

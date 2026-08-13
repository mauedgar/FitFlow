"""Registro explícito de los modelos ORM activos de FitFlow."""

from app.db.models.booking import Booking
from app.db.models.class_schedule import ClassSchedule
from app.db.models.class_session import ClassSession
from app.db.models.client import Client
from app.db.models.gym_class import GymClass
from app.db.models.membership import Membership
from app.db.models.person import Person
from app.db.models.teacher import Teacher
from app.db.models.user import User

__all__ = [
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

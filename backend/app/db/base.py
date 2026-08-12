# Este archivo centraliza los modelos para que Alembic los descubra.

from app.db.base_class import Base  # noqa: F401
from backend.app.db.models.booking import Booking  # noqa: F401
from backend.app.db.models.class_schedule import ClassSchedule  # noqa: F401
from backend.app.db.models.class_session import ClassSession  # noqa: F401
from backend.app.db.models.client import Client  # noqa: F401
from backend.app.db.models.gym_class import GymClass  # noqa: F401
from backend.app.db.models.membership import Membership  # noqa: F401
from backend.app.db.models.person import Person  # noqa: F401
from backend.app.db.models.teacher import Teacher  # noqa: F401

# Importa todos tus modelos aquí
from backend.app.db.models.user import User  # noqa: F401

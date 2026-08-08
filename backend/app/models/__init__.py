"""Model package for FitFlow backend."""

# Este archivo hace que sea más fácil importar tus modelos desde otros lugares.
from app.models.booking import Booking  # noqa: F401
from app.models.class_schedule import ClassSchedule  # noqa: F401
from app.models.class_session import ClassSession  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.gym_class import GymClass  # noqa: F401
from app.models.membership import Membership  # noqa: F401
from app.models.permission import Permission  # noqa: F401
from app.models.person import Person  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.user import User  # noqa: F401

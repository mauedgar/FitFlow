"""Model package for FitFlow backend."""

# Este archivo hace que sea más fácil importar tus modelos desde otros lugares.
from backend.app.db.models.booking import Booking  # noqa: F401
from backend.app.db.models.class_schedule import ClassSchedule  # noqa: F401
from backend.app.db.models.class_session import ClassSession  # noqa: F401
from backend.app.db.models.client import Client  # noqa: F401
from backend.app.db.models.gym_class import GymClass  # noqa: F401
from backend.app.db.models.membership import Membership  # noqa: F401
from backend.app.db.models.permission import Permission  # noqa: F401
from backend.app.db.models.person import Person  # noqa: F401
from backend.app.db.models.role import Role  # noqa: F401
from backend.app.db.models.teacher import Teacher  # noqa: F401
from backend.app.db.models.user import User  # noqa: F401

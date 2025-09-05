# Este archivo centraliza los modelos para que Alembic los descubra.

from app.db.base_class import Base          # noqa: F401
# Importa todos tus modelos aquí
from app.models.user import User            # noqa: F401
from app.models.teacher import Teacher      # noqa: F401
from app.models.gym_class import GymClass  # noqa: F401
from app.models.client import Client        # noqa: F401

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum as SQLAlchemyEnum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ActivityType, DifficultyLevel
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.class_schedule import ClassSchedule


class GymClass(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Catálogo base de actividades del gimnasio.

    Esta entidad representa la definición abstracta de una actividad
    reservable, como por ejemplo:
    - una clase grupal (CrossFit WOD, Yoga, Funcional),
    - una franja de musculación,
    - o una sesión de entrenamiento personalizado.

    La lógica operativa concreta (profesor, horario, plan permitido,
    capacidad efectiva y generación de sesiones futuras) se delega a
    ClassSchedule y ClassSession.
    """

    __tablename__ = "gym_classes"

    # Identificador único de la actividad dentro del catálogo.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Nombre visible de la actividad.
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Descripción comercial o informativa de la actividad.
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Tipo de actividad ofrecida.
    activity_type: Mapped[ActivityType] = mapped_column(
        SQLAlchemyEnum(ActivityType, name="activitytype"),
        nullable=False,
    )

    # Duración sugerida por defecto para la actividad, expresada en minutos.
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Nivel de dificultad asociado a la actividad.
    # En actividades como musculación libre, puede evaluarse si este campo
    # debe ser opcional según la lógica final del producto.
    difficulty: Mapped[DifficultyLevel | None] = mapped_column(
        SQLAlchemyEnum(DifficultyLevel, name="difficultylevel"),
        nullable=True,
    )

    # Capacidad sugerida por defecto. El cupo operativo real se define
    # posteriormente en ClassSchedule y se replica en ClassSession.
    default_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )

    # Imagen opcional para enriquecer la presentación visual del catálogo.
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relación con los horarios recurrentes en los que esta actividad se ofrece.
    class_schedules: Mapped[list["ClassSchedule"]] = relationship(
        "ClassSchedule",
        back_populates="gym_class",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "duration_minutes >= 1", name="ck_gym_class_duration_positive"
        ),
        CheckConstraint(
            "default_capacity >= 1", name="ck_gym_class_capacity_positive"
        ),
    )

import uuid
import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Date, Time, Integer, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, ActiveMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .gym_class import GymClass
    from .class_session import ClassSession
    from .teacher import Teacher


class AllowedPlan(str, enum.Enum):
    """
    Planes de membresía habilitados para una oferta recurrente.

    Este enum permite restringir qué tipo de cliente puede reservar
    las sesiones generadas a partir de este horario.
    """
    BASIC = "basic"
    PREMIUM = "premium"
    PERSONALIZED = "personalized"


class ClassSchedule(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """
    Configuración recurrente de una clase dentro de la agenda del gimnasio.

    Esta entidad representa una oferta operativa concreta:
    - qué clase se ofrece
    - qué profesor la dicta
    - en qué días de la semana ocurre
    - en qué horario comienza
    - cuánto dura
    - qué capacidad máxima tiene
    - durante qué período está vigente
    - qué plan de membresía puede reservarla

    A partir de este modelo se generan las ClassSession concretas
    que luego podrán visualizarse y reservarse en la agenda.
    """
    __tablename__ = "class_schedules"

    # Identificador único de la configuración recurrente.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Clase del catálogo asociada a esta oferta recurrente.
    gym_class_id = Column(
        UUID(as_uuid=True),
        ForeignKey("gym_classes.id", ondelete="CASCADE"),
        nullable=False
    )

    # Profesor responsable de dictar esta oferta.
    teacher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Días de la semana en los que se repite la clase.
    # Ejemplo: [0, 2, 4] para lunes, miércoles y viernes.
    days_of_week = Column(JSONB, nullable=False)

    # Hora de inicio de la clase dentro del patrón recurrente.
    start_time = Column(Time(timezone=False), nullable=False)

    # Duración de la clase expresada en minutos.
    duration_minutes = Column(Integer, nullable=False)

    # Capacidad máxima por sesión generada a partir de este horario.
    capacity = Column(Integer, nullable=False, default=10)

    # Fecha desde la cual este horario entra en vigencia.
    start_date = Column(Date, nullable=False)

    # Fecha hasta la cual este horario se mantiene vigente.
    # Si es null, el horario se considera abierto o indefinido.
    end_date = Column(Date, nullable=True)

    # Restricción opcional por plan de membresía.
    # Si es null, la oferta no tiene restricción de plan.
    allowed_plan = Column(
        SQLAlchemyEnum(AllowedPlan, name="allowedplan"),
        nullable=True
    )

    # Relación con la clase del catálogo.
    gym_class: Mapped["GymClass"] = relationship(
        "GymClass",
        back_populates="class_schedules"
    )

    # Relación con el profesor asignado.
    teacher: Mapped["Teacher"] = relationship(
        "Teacher",
        back_populates="class_schedules"
    )

    # Relación con las sesiones concretas generadas a partir de este horario.
    class_sessions: Mapped[List["ClassSession"]] = relationship(
        "ClassSession",
        back_populates="class_schedule",
        cascade="all, delete-orphan"
    )
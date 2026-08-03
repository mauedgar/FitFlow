import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base
from app.db.mixins import ActiveMixin, TimestampMixin

from ..core.enums import ClassSessionStatus

if TYPE_CHECKING:
    from .booking import Booking
    from .class_schedule import ClassSchedule


class ClassSession(Base, TimestampMixin, ActiveMixin):
    """
    Ocurrencia concreta y reservable de una actividad en una fecha y hora específicas.

    Esta entidad se genera a partir de un ClassSchedule recurrente y representa
    una sesión real del calendario. Es la unidad sobre la que el cliente reserva,
    el staff hace check-in y el sistema controla cupos y asistencia.
    """
    __tablename__ = "class_sessions"

    # Identificador único de la sesión concreta.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Referencia al horario recurrente que originó esta sesión.
    class_schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("class_schedules.id", ondelete="CASCADE"),
        nullable=False
    )

    # Fecha y hora exacta de inicio de la sesión.
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Fecha y hora exacta de finalización de la sesión.
    ends_at = Column(DateTime(timezone=True), nullable=False)

    # Capacidad máxima heredada del schedule al momento de generar la sesión.
    # Se guarda como snapshot para evitar inconsistencias si el schedule cambia luego.
    capacity_snapshot = Column(Integer, nullable=False)

    # Estado operativo de la sesión concreta.
    status = Column(
        SQLAlchemyEnum(ClassSessionStatus, name="classsessionstatus"),
        nullable=False,
        default=ClassSessionStatus.scheduled
    )

    # Relación con el horario recurrente de origen.
    class_schedule: Mapped["ClassSchedule"] = relationship(
        "ClassSchedule",
        back_populates="class_sessions"
    )

    # Reservas asociadas a esta sesión concreta.
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="class_session"
    )

    # Evita duplicar dos sesiones con el mismo schedule y la misma fecha/hora de inicio.
    __table_args__ = (
        UniqueConstraint(
            "class_schedule_id",
            "starts_at",
            name="uq_class_schedule_starts_at"
        ),
    )
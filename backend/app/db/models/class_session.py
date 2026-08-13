import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import BookingStatus, ClassSessionStatus
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, TimestampMixin
from app.db.models.booking import Booking

if TYPE_CHECKING:
    from app.db.models.class_schedule import ClassSchedule


class ClassSession(Base, TimestampMixin, ActiveMixin):
    """Ocurrencia concreta y reservable de una actividad en una fecha y hora específicas.

    Esta entidad se genera a partir de un ClassSchedule recurrente y representa
    una sesión real del calendario. Es la unidad sobre la que el cliente reserva,
    el staff hace check-in y el sistema controla cupos y asistencia.
    """

    __tablename__ = "class_sessions"

    # Identificador único de la sesión concreta.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Referencia al horario recurrente que originó esta sesión.
    class_schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("class_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Fecha y hora exacta de inicio de la sesión.
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Fecha y hora exacta de finalización de la sesión.
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Capacidad máxima heredada del schedule al momento de generar la sesión.
    # Se guarda como snapshot para evitar inconsistencias si el schedule cambia luego.
    capacity_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)

    # Estado operativo de la sesión concreta.
    status: Mapped[ClassSessionStatus] = mapped_column(
        SQLAlchemyEnum(ClassSessionStatus, name="classsessionstatus"),
        nullable=False,
        default=ClassSessionStatus.scheduled,
    )

    # Relación con el horario recurrente de origen.
    class_schedule: Mapped["ClassSchedule"] = relationship(
        "ClassSchedule",
        back_populates="class_sessions",
        lazy="raise",
    )

    # Reservas asociadas a esta sesión concreta.
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="class_session",
        lazy="raise",
    )

    # Evita duplicar dos sesiones con el mismo schedule y la misma fecha/hora de inicio.
    __table_args__ = (
        UniqueConstraint(
            "class_schedule_id",
            "starts_at",
            name="uq_class_schedule_starts_at",
        ),
    )
    # ------------------------------------------------------------------ #
    # Propiedades híbridas (calculadas)
    # ------------------------------------------------------------------ #

    @hybrid_property
    def current_bookings_count(self) -> int: # type: ignore[misc]
        """Cantidad actual de reservas confirmadas para esta sesión."""
        return sum(
            booking.status != BookingStatus.cancelled for booking in self.bookings
        )

    @current_bookings_count.expression  # type: ignore[misc]
    def current_bookings_count(cls):  # noqa: ANN201, N805
        """Versión SQL para usar en queries."""
        return (
            select(func.count(Booking.id))
            .where(
                Booking.class_session_id == cls.id,
                Booking.status != BookingStatus.cancelled,
            )
            .correlate(cls)  # type: ignore[arg-type]
            .scalar_subquery()
        )

    @hybrid_property
    def available_spots(self) -> int:
        """Cantidad de lugares disponibles en la sesión."""
        return max(self.capacity_snapshot - self.current_bookings_count, 0) # pyright: ignore[reportReturnType]

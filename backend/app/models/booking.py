import uuid
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, ActiveMixin

if TYPE_CHECKING:
    from .client import Client
    from .class_session import ClassSession


class BookingStatus(str, enum.Enum):
    """
    Estados posibles de una reserva.

    - confirmed: la reserva fue creada correctamente y el cupo quedó tomado.
    - cancelled: la reserva fue cancelada por el cliente o por el staff.
    - attended: el cliente realizó check-in y asistió efectivamente.
    - no_show: el cliente tenía reserva, pero no asistió.
    """
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class Booking(Base, TimestampMixin, ActiveMixin):
    """
    Reserva concreta de un cliente para una sesión específica.

    Esta entidad vincula a un cliente con una ClassSession determinada.
    A partir de esta relación se controla:
    - la ocupación de cupos,
    - la asistencia,
    - las cancelaciones,
    - y el historial operativo del cliente.
    """
    __tablename__ = "bookings"

    # Identificador único de la reserva.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cliente que realiza la reserva.
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False
    )

    # Sesión concreta reservada por el cliente.
    class_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Estado actual de la reserva.
    status = Column(
        SQLAlchemyEnum(BookingStatus, name="bookingstatus"),
        nullable=False,
        default=BookingStatus.CONFIRMED
    )

    # Momento en que el cliente realizó efectivamente el check-in.
    checked_in_at = Column(DateTime(timezone=True), nullable=True)

    # Momento en que la reserva fue cancelada, si corresponde.
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relación con el cliente titular de la reserva.
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="bookings"
    )

    # Relación con la sesión concreta reservada.
    class_session: Mapped["ClassSession"] = relationship(
        "ClassSession",
        back_populates="bookings"
    )

    # Un cliente no puede reservar dos veces la misma sesión.
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "class_session_id",
            name="uq_booking_client_session"
        ),
    )
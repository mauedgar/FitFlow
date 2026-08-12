import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.core.enums import BookingStatus
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.class_session import ClassSession
    from app.models.client import Client



class Booking(Base, TimestampMixin, ActiveMixin):
    """Reserva concreta de un cliente para una sesión específica.

    Esta entidad vincula a un cliente con una ClassSession determinada.
    A partir de esta relación se controla:
    - la ocupación de cupos,
    - la asistencia,
    - las cancelaciones,
    - y el historial operativo del cliente.
    """

    __tablename__ = "bookings"  # pyright: ignore[reportAssignmentType]

    # Identificador único de la reserva.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cliente que realiza la reserva.
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Sesión concreta reservada por el cliente.
    class_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Estado actual de la reserva.
    status = Column(
        SQLAlchemyEnum(BookingStatus, name="bookingstatus"),
        nullable=False,
        default=BookingStatus.confirmed,
    )

    # Momento en que el cliente realizó efectivamente el check-in.
    checked_in_at = Column(DateTime(timezone=True), nullable=True)

    # Momento en que la reserva fue cancelada, si corresponde.
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relación con el cliente titular de la reserva.
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="bookings",
    )

    # Relación con la sesión concreta reservada.
    class_session: Mapped["ClassSession"] = relationship(
        "ClassSession",
        back_populates="bookings",
    )

    # Un cliente no puede reservar dos veces la misma sesión.
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "class_session_id",
            name="uq_booking_client_session",
        ),
    )
# última línea de código.

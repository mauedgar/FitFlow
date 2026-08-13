import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import BookingStatus
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.class_session import ClassSession
    from app.db.models.client import Client



class Booking(Base, TimestampMixin, ActiveMixin):
    """Reserva concreta de un cliente para una sesión específica.

    Esta entidad vincula a un cliente con una ClassSession determinada.
    A partir de esta relación se controla:
    - la ocupación de cupos,
    - la asistencia,
    - las cancelaciones,
    - y el historial operativo del cliente.
    """

    __tablename__ = "bookings"

    # Identificador único de la reserva.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Cliente que realiza la reserva.
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Sesión concreta reservada por el cliente.
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("class_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Estado actual de la reserva.
    status: Mapped[BookingStatus] = mapped_column(
        SQLAlchemyEnum(BookingStatus, name="bookingstatus"),
        nullable=False,
        default=BookingStatus.confirmed,
    )

    # Momento en que el cliente realizó efectivamente el check-in.
    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Momento en que la reserva fue cancelada, si corresponde.
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relación con el cliente titular de la reserva.
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="bookings",
        lazy="raise",
    )

    # Relación con la sesión concreta reservada.
    class_session: Mapped["ClassSession"] = relationship(
        "ClassSession",
        back_populates="bookings",
        lazy="raise",
    )

    # Un cliente no puede reservar dos veces la misma sesión.
    __table_args__ = (
        Index(
            "uq_booking_active_client_session",
            "client_id",
            "class_session_id",
            unique=True,
            postgresql_where=status != BookingStatus.cancelled,
        ),
    )

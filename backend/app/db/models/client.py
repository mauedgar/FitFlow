import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .person import Person

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.membership import Membership


class Client(Person):
    """Perfil de cliente del gimnasio.

    Esta entidad extiende a Person y representa a un usuario que puede:
    - tener una membresía,
    - realizar reservas,
    - hacer check-in,
    - y participar de actividades agendadas.
    """

    __tablename__ = "clients"

    # La clave primaria coincide con el registro base de Person.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True
    )

    # Reservas realizadas por el cliente.
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    # Membresía activa o principal del cliente.
    membership: Mapped["Membership | None"] = relationship(
        "Membership",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="raise",
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "client",
    }

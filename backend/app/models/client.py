from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from .person import Person

if TYPE_CHECKING:
    from .booking import Booking
    from .membership import Membership


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
    id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True)

    # Reservas realizadas por el cliente.
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    # Membresía activa o principal del cliente.
    membership: Mapped["Membership"] = relationship(
        "Membership",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "client",
    }

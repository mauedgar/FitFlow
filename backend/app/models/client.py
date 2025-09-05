from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .person import Person # Hereda de Person

class Client(Person):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True)

    # --- Relación Uno-a-Uno con Membership ---
    # Un cliente tiene una única membresía activa.
    # `cascade` asegura que si se borra un cliente, su membresía también se borra.
    membership = relationship(
        "Membership", 
        back_populates="client", 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        "polymorphic_identity": "client",
    }
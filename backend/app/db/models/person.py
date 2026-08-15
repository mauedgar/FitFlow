import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Person(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Entidad base de identidad personal dentro del sistema.

    Esta tabla concentra los datos personales comunes de cualquier
    individuo registrado en la plataforma, independientemente de su rol
    operativo posterior (cliente, profesor, etc.).

    La autenticación se resuelve en User, mientras que la especialización
    funcional se implementa mediante herencia con Client y Teacher.
    """

    __tablename__ = "persons"

    # Identificador único de la persona.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    # Nombre de pila de la persona.
    first_name: Mapped[str] = mapped_column(String, index=True, nullable=False)

    # Apellido de la persona.
    last_name: Mapped[str] = mapped_column(String, index=True, nullable=False)

    # Número de documento identificatorio personal (DNI, cédula, pasaporte, etc.).
    document_number: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True,
    )

    # Domicilio o dirección declarada.
    address: Mapped[str | None] = mapped_column(String, nullable=True)

    # Ruta o URL al apto físico o certificado médico, si aplica.
    medical_fit_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Ruta o URL de la imagen de perfil.
    profile_image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relación uno a uno con la cuenta autenticable del sistema.
    # Esta separación permite desacoplar credenciales de acceso
    # respecto de la identidad personal.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="person_profile",
        lazy="raise",
    )

    # Discriminador polimórfico para la herencia ORM.
    # Permite distinguir si la persona es una base genérica,
    # un cliente o un profesor.
    person_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "person",
        "polymorphic_on": person_type,
    }

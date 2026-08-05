import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, Enum as SQLAlchemyEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin
from backend.app.core.enums import UserRole

if TYPE_CHECKING:
    from .person import Person

class User(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Cuenta autenticable del sistema.

    Esta entidad concentra la información necesaria para login,
    autorización y control de acceso. Los datos personales y la
    especialización funcional se delegan a Person y sus subclases.
    """

    __tablename__ = "users" # pyright: ignore[reportAssignmentType]

    # Identificador único del usuario autenticable.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email único utilizado como credencial principal de acceso.
    email = Column(String, unique=True, index=True, nullable=False)

    # Contraseña hasheada del usuario.
    hashed_password = Column(String, nullable=False)

    # Rol principal del usuario dentro del sistema.
    role = Column(
        SQLAlchemyEnum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.client,
    )

    # Relación uno a uno con el perfil personal del usuario.
    person_profile: Mapped["Person"] = relationship(
        "Person",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Representación legible del usuario para debugging y logs."""
        return f"<User(email='{self.email}', role='{self.role}')>"

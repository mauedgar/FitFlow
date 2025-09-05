import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    surname = Column(String, index=True, nullable=False)
    passport = Column(String, unique=True, index=True, nullable=True) # DNI, Cédula, etc.
    address = Column(String, nullable=True)
    
    # Rutas a los archivos. La lógica de subida de archivos es para otro sprint.
    medical_fit_url = Column(String, nullable=True)
    profile_img_url = Column(String, nullable=True)

    # --- Relación Uno-a-Uno con User ---
    # Esto vincula el perfil de la persona con sus credenciales de login.
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="person_profile")

    # --- Discriminador para la Herencia ---
    # Esta columna le dice a SQLAlchemy qué tipo de Persona es cada fila.
    type = Column(String(50))

    __mapper_args__ = {
        "polymorphic_identity": "person",
        "polymorphic_on": type,
    }
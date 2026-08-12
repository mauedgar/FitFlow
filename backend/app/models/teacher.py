from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.person import Person

if TYPE_CHECKING:
    from .class_schedule import ClassSchedule


class Teacher(Person):
    """Perfil de profesor o entrenador del gimnasio.

    Esta entidad extiende a Person y representa a quienes dictan
    actividades dentro de la agenda operativa del sistema.
    """

    __tablename__ = "teachers"

    # La clave primaria coincide con el registro base de Person.
    id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True)

    # Identificador fiscal o laboral del profesor, si aplica.
    cuil = Column(String, unique=True, index=True, nullable=True)

    # Biografía o descripción breve del perfil profesional.
    bio = Column(String, nullable=True)
    @property
    def full_name(self) -> str:
        """Nombre completo."""
        return f"{self.first_name} {self.last_name}"
    # Horarios recurrentes asignados al profesor.
    class_schedules: Mapped[list["ClassSchedule"]] = relationship(
        "ClassSchedule",
        back_populates="teacher",
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "teacher",
    }

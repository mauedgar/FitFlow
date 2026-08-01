from typing import TYPE_CHECKING, List

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID

from .person import Person

if TYPE_CHECKING:
    from .class_schedule import ClassSchedule


class Teacher(Person):
    """
    Perfil de profesor o entrenador del gimnasio.

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

    # Horarios recurrentes asignados al profesor.
    class_schedules: Mapped[List["ClassSchedule"]] = relationship(
        "ClassSchedule",
        back_populates="teacher"
    )

    __mapper_args__ = {
        "polymorphic_identity": "teacher",
    }
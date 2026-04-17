import uuid
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from .person import Person
from .gym_class import teacher_class_association
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .class_schedule import ClassSchedule
    from .gym_class import GymClass
class Teacher(Person):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), primary_key=True, default=uuid.uuid4)
    cuil = Column(String, unique=True, index=True, nullable=True) # Opcional al principio
    bio = Column(String, nullable=True)
    
    class_schedules: Mapped["ClassSchedule"] = relationship("ClassSchedule", back_populates="teacher")

     # --- Relación Many-to-Many con GymClass (sin cambios) ---
    classes: Mapped[List["GymClass"]] = relationship(
        "GymClass",
        secondary=teacher_class_association,
        back_populates="teachers"
    )

    # --- Mapeo de Herencia ---
    # Esto le dice a SQLAlchemy que las filas con 'type'="teacher" son de esta clase.
    __mapper_args__ = {
        "polymorphic_identity": "teacher",
    }

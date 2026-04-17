import uuid
import enum
from sqlalchemy import Column, String, Integer, Enum as SQLAlchemyEnum, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .class_schedule import ClassSchedule
    from .teacher import Teacher


# Clave Primaria Compuesta: asegura que un par (teacher_id, gym_class_id) sea único.
teacher_class_association = Table(
    "teacher_class_association",
    Base.metadata,
    Column("teacher_id", UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    Column("gym_class_id", UUID(as_uuid=True), ForeignKey("gym_classes.id", ondelete="CASCADE"), primary_key=True),
)
# Definimos un Enum de Python para los niveles de dificultad.
# Heredar de 'str' ayuda con la serialización en Pydantic/FastAPI.
class DifficultyLevel(str, enum.Enum):
    BEGINNER = "Principante"
    INTERMEDIATE = "Intermedio"
    ADVANCED = "Avanzado"

class GymClass(Base):
    __tablename__ = "gym_classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)    
    # Usamos el Enum que definimos para restringir los valores en esta columna.
    difficulty = Column(SQLAlchemyEnum(DifficultyLevel), nullable=True)    
    # ⭐ 'capacity' se moverá principalmente a ClassSchedule, pero podemos dejar un 'default_capacity' aquí
    default_capacity = Column(Integer, nullable=False, default=10)
    # --- Relaciones Many-to-Many con Teachers (si es necesario a nivel de definición) ---
    # Si un GymClass puede ser impartido por varios teachers en *diferentes ofertas*
    # esta tabla de asociación podría incluso volverse redundante y la relación directa sería via ClassSchedule.
    # Por ahora, la mantengo si la usas para mostrar "quién puede dar qué clase".
    # Pero la relación principal entre un teacher y una *oferta específica* de clase será en ClassSchedule.
    class_schedules: Mapped[List["ClassSchedule"]] = relationship("ClassSchedule", back_populates="gym_class", cascade="all, delete-orphan")

    # --- CAMBIO A MANY-TO-MANY ---
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher",
        secondary=teacher_class_association,
        back_populates="classes"
    )

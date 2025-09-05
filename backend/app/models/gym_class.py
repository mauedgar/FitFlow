import uuid
import enum
from sqlalchemy import Column, DateTime, String, Integer, Enum as SQLAlchemyEnum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base


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
    schedule = Column(DateTime(timezone=True), nullable=True)

   
    # --- CAMBIO A MANY-TO-MANY ---
    teachers = relationship(
        "Teacher",
        secondary=teacher_class_association,
        back_populates="classes"
    )

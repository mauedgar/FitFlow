import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Importamos el Enum del modelo para mantener la consistencia
from app.models.gym_class import DifficultyLevel

# --- MANEJO DE REFERENCIAS CIRCULARES ---
# Para evitar errores de importación (gym_class importa teacher y teacher importa gym_class),
# importaremos el schema de Teacher de una manera especial.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .teacher import TeacherInClassResponse

# --- ESQUEMAS BASE ---
class GymClassBase(BaseModel):
    name: str
    description: str
    duration_minutes: int
    difficulty: DifficultyLevel
    schedule: datetime

# --- ESQUEMA PARA CREACIÓN ---
# Ahora espera una LISTA de UUIDs de profesores.
class GymClassCreate(GymClassBase):
    teacher_ids: List[uuid.UUID] = Field(..., min_length=1, description="Lista de IDs de los profesores que imparten la clase. Debe tener al menos uno.")

# --- ESQUEMA PARA ACTUALIZACIÓN ---
class GymClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    teacher_ids: Optional[List[uuid.UUID]] = None
    schedule: Optional[datetime] = None


# --- ESQUEMA DE RESPUESTA PRINCIPAL ---
# Este es el objeto completo de la clase que se devuelve en la API.
class GymClass(GymClassBase):
    id: uuid.UUID
    # Devuelve una LISTA de objetos Teacher completos.
    # Usamos "Teacher" como string (referencia a futuro) para evitar la importación circular.
    teachers: List["TeacherInClassResponse"] = []

    class Config:
        from_attributes = True

# --- ESQUEMA PARA RESPUESTAS ANIDADAS ---
# Este es el que ya habías creado. Es perfecto para usar dentro de la respuesta de Teacher.
class GymClassInTeacherResponse(GymClassBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
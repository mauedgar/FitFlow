import uuid
from typing import List, Optional

from .person import PersonBase, PersonCreate, PersonUpdate
from .gym_class import GymClassInTeacherResponse # Para la relación many-to-many
# GymClass.model_rebuild() /cambios en init

# --- Esquema para CREAR el perfil de un Profesor ---
# Hereda todos los campos de persona que se necesitan al crear.
class TeacherCreate(PersonCreate):
    # Añadimos solo los campos específicos de Teacher.
    bio: Optional[str] = None
    cuil: Optional[str] = None

# --- Esquema para ACTUALIZAR el perfil de un Profesor ---
# Hereda de PersonUpdate, que ya tiene los campos de persona como opcionales.
class TeacherUpdate(PersonUpdate):
    bio: Optional[str] = None
    cuil: Optional[str] = None
    # Aquí podríamos añadir más campos si fuera necesario, como teacher_ids para las clases.

# --- Esquema de RESPUESTA de la API ---
# Este es el objeto completo que se devuelve. Hereda los datos base de Person.
class Teacher(PersonBase):
    id: uuid.UUID
    bio: Optional[str] = None
    cuil: Optional[str] = None
    classes: List[GymClassInTeacherResponse] = [] # La relación con las clases

    # La configuración 'from_attributes' se hereda de PersonBase,
    # por lo que no es necesario repetirla aquí.

# Muestra la información del profesor SIN su lista de clases para evitar la repetición.
class TeacherInClassResponse(PersonBase):
    id: uuid.UUID
    bio: Optional[str] = None
    cuil: Optional[str] = None
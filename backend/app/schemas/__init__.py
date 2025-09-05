# Importa los esquemas que ya tenías para el usuario
from .user import UserBase, UserCreate, UserResponse, UserUpdate  # noqa: F401
from .token import Token, TokenData      # noqa: F401
# Agrega los nuevos esquemas para que sean fácilmente accesibles
from .teacher import Teacher, TeacherCreate, TeacherUpdate, TeacherInClassResponse      # noqa: F401
from .gym_class import GymClass, GymClassCreate, GymClassUpdate, GymClassInTeacherResponse   # noqa: F401
from .person import PersonBase, PersonCreate, PersonUpdate           # noqa: F401
GymClass.model_rebuild()
Teacher.model_rebuild()
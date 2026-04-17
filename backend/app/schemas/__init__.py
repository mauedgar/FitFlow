# Importa los esquemas que ya tenías para el usuario
from .user import UserBase, UserCreate, UserResponse, UserUpdate  # noqa: F401
from .token import Token, TokenPayload      # noqa: F401
# Agrega los nuevos esquemas para que sean fácilmente accesibles
from .teacher import Teacher, TeacherCreate, TeacherUpdate, TeacherInClassScheduleResponse , TeacherInClassResponse, TeacherInScheduleResponseMini     # noqa: F401
from .gym_class import GymClass, GymClassCreate, GymClassUpdate, GymClassInTeacherResponse, GymClassInClassScheduleResponse, GymClassInClassScheduleResponseMini, GymClassWithSchedules   # noqa: F401
from .person import PersonBase, PersonCreate, PersonUpdate           # noqa: F401
from .booking import Booking, BookingCreate, BookingUpdate, BookingStatus, BookingInClassSessionResponse, BookingInClientResponse, BookingCreateInternal   #noqa: F401
from .class_session import ClassSession, ClassSessionCreate, ClassSessionUpdate, ClassSessionInBookingResponse, ClassSessionInResponse #noqa: F401
from .class_schedule import ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate, ClassScheduleInClassSessionResponse, ClassScheduleInResponse, ClassScheduleWithNextSession #noqa: F401
from .client import Client, ClientCreate, ClientUpdate, ClientInBookingResponse #noqa: F401
from .membership import Membership      #noqa: F401

GymClass.model_rebuild()
GymClassInClassScheduleResponse.model_rebuild()
Teacher.model_rebuild()

ClassSchedule.model_rebuild()
ClassScheduleWithNextSession.model_rebuild()
GymClassWithSchedules.model_rebuild()

ClassSession.model_rebuild()
Booking.model_rebuild()
Client.model_rebuild()
Membership.model_rebuild()

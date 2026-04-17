# app/schemas/class_schedule.py
import uuid
from datetime import time, date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# Para evitar referencias circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .gym_class import GymClassInClassScheduleResponse, GymClassInClassScheduleResponseMini
    from .teacher import TeacherInClassScheduleResponse, TeacherInScheduleResponseMini
    from .class_session import ClassSessionInResponse # Las sesiones que derivan de este horario

# --- Esquema Base ---
class ClassScheduleBase(BaseModel):
    days_of_week: List[int] = Field(..., description="Días de la semana (0=Lunes, 6=Domingo)", min_length=1, max_length=7)
    start_time: time
    end_time: time
    max_capacity: int = Field(..., ge=1, description="Capacidad máxima para cada sesión de esta oferta")
    start_date: date
    end_date: Optional[date] = None # Si es None, la oferta es indefinida

# --- Esquema para CREACIÓN ---
class ClassScheduleCreate(ClassScheduleBase):
    gym_class_id: uuid.UUID
    teacher_id: uuid.UUID

# --- Esquema para ACTUALIZACIÓN ---
class ClassScheduleUpdate(BaseModel):
    days_of_week: Optional[List[int]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_capacity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gym_class_id: Optional[uuid.UUID] = None # Podría ser posible reasignar la clase
    teacher_id: Optional[uuid.UUID] = None # Podría ser posible reasignar el profesor

# --- Esquema de RESPUESTA de la API ---
class ClassSchedule(ClassScheduleBase):
    id: uuid.UUID
    gym_class_id: uuid.UUID
    teacher_id: uuid.UUID

    # Incluimos los objetos completos de GymClass, Teacher y las sesiones futuras
    gym_class: "GymClassInClassScheduleResponse"
    teacher: "TeacherInClassScheduleResponse"
    
    # Solo las sesiones futuras (o un subconjunto) para evitar cargar todas las sesiones históricas
    # La lógica para filtrar esto se haría en el endpoint
    future_sessions: List["ClassSessionInResponse"] = [] 

    class Config:
        from_attributes = True

# --- Esquema para Respuestas Anidadas (ej. dentro de GymClass o Teacher) ---
class ClassScheduleInResponse(ClassScheduleBase):
    id: uuid.UUID
    gym_class_id: uuid.UUID
    teacher_id: uuid.UUID
    teacher: "TeacherInClassScheduleResponse"
    # No incluir las relaciones completas para evitar bucles o sobrecarga
    class Config:
        from_attributes = True

class ClassScheduleInClassSessionResponse(BaseModel): # Usado cuando ClassSchedule se lista dentro de ClassSession
    gym_class: "GymClassInClassScheduleResponseMini"
    teacher: "TeacherInScheduleResponseMini"
    # No incluir otras relaciones aquí para mantenerlo ligero
    class Config:
        from_attributes = True

# NUEVO ESQUEMA: para la información calculada
class NextSessionInfo(BaseModel):
    start_datetime: datetime
    available_spots: int

# NUEVO ESQUEMA: extiende el ClassSchedule normal para incluir la nueva info
class ClassScheduleWithNextSession(ClassSchedule): # Asume que tienes un schema ClassSchedule
    next_upcoming_session: Optional[NextSessionInfo] = None

# app/schemas/class_session.py
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

# Para evitar referencias circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .class_schedule import ClassSchedule, ClassScheduleInClassSessionResponse
    from .booking import BookingInClassSessionResponse

# --- Esquema Base ---
class ClassSessionBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    is_cancelled: bool = False

# --- Esquema para CREACIÓN (principalmente para el generador interno) ---
class ClassSessionCreate(ClassSessionBase):
    class_schedule_id: uuid.UUID

# --- Esquema para ACTUALIZACIÓN ---
class ClassSessionUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_cancelled: Optional[bool] = None
    # No permitir cambiar class_schedule_id directamente via update

# --- Esquema de RESPUESTA de la API ---
class ClassSession(ClassSessionBase):
    id: uuid.UUID
    class_schedule_id: uuid.UUID
    
    # Incluimos la relación con ClassSchedule y Bookings
    class_schedule: "ClassSchedule"
    bookings: List["BookingInClassSessionResponse"] = []
    
    # Campo calculado para la disponibilidad
    current_bookings_count: int = 0
    available_spots: int = 0 # Se calculará en el endpoint/servicio

    class Config:
        from_attributes = True

# --- Esquema para Respuestas Anidadas (ej. dentro de ClassSchedule o GymClass) ---
class ClassSessionInResponse(ClassSessionBase):
    id: uuid.UUID
    class_schedule_id: uuid.UUID
    
    # Campos calculados para la disponibilidad (solo lectura)
    current_bookings_count: int = 0
    available_spots: int = 0

    class Config:
        from_attributes = True

class ClassSessionInBookingResponse(ClassSessionBase): # Usado cuando ClassSession se lista dentro de Booking
    id: uuid.UUID
    class_schedule_id: uuid.UUID
    class_schedule: "ClassScheduleInClassSessionResponse"

    # No incluir otras relaciones aquí para mantenerlo ligero
    class Config:
        from_attributes = True

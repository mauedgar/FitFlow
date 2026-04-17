# app/crud/crud_booking.py
from app.crud.base import CRUDBase
from app.models import Booking
from app.schemas import BookingCreate, BookingUpdate

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    # El CRUD base es suficiente. La lógica de negocio más compleja (capacidad,
    # verificar reservas existentes) se maneja en el endpoint de la API.
    pass

booking = CRUDBooking(Booking)
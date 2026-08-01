# app/schemas/client.py
import uuid
from typing import List, Optional
# Importamos esquemas de Booking para la relación.
# Usamos TYPE_CHECKING para evitar circularidad si Booking también importa Client.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .booking import BookingInClientResponse
from .membership import Membership
# Asumo que tienes un esquema base para Person de donde hereda Client
from .person import PersonBase, PersonCreate, PersonUpdate

# --- Esquema Base ---
# Hereda de PersonBase
class ClientBase(PersonBase):
    pass # No hay campos adicionales específicos de Client en la base, más allá de PersonBase

# --- Esquema para CREAR ---
# Hereda de PersonCreate
class ClientCreate(PersonCreate):
    pass # No hay campos adicionales específicos de Client al crear

# --- Esquema para ACTUALIZAR ---
# Hereda de PersonUpdate
class ClientUpdate(PersonUpdate):
    pass # No hay campos adicionales específicos de Client al actualizar

# --- Esquema de RESPUESTA de la API ---
class Client(ClientBase):
    id: uuid.UUID
    # Añadimos la relación con Bookings
    bookings: List["BookingInClientResponse"] = []
    # Añadimos la relación con Membership (si tienes un esquema Membership)
    membership: Optional["Membership"] = None # Usar esto si quieres mostrar el objeto completo

    class Config:
        from_attributes = True

# --- Esquema para Respuestas Anidadas (ej. dentro de Booking) ---
class ClientInBookingResponse(ClientBase):
    id: uuid.UUID
    # No incluir otras relaciones aquí para mantenerlo ligero
    class Config:
        from_attributes = True

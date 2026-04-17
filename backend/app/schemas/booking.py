# app/schemas/booking.py
"""
Módulo de esquemas Pydantic para la entidad 'Booking'.

Este archivo define las diferentes "formas" o "contratos" de datos que la entidad Booking
puede adoptar a lo largo del ciclo de vida de una petición API, siguiendo las mejores
prácticas para FastAPI y Pydantic.

Se separa la lógica en:
- Base: Atributos comunes.
- Create: Datos esperados para la creación de un nuevo recurso.
- Update: Datos opcionales para la actualización parcial (PATCH).
- Response (Booking): El objeto completo que se devuelve al cliente, incluyendo relaciones.
- Schemas anidados: Versiones simplificadas para evitar la recursión infinita en las respuestas.
- Schemas internos: Para la comunicación entre capas de la aplicación.
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, model_validator

# Se importa el Enum directamente desde el modelo para mantener una única fuente de verdad.
from app.models.booking import BookingStatus

# El bloque TYPE_CHECKING previene importaciones circulares en tiempo de ejecución.
# El código dentro de este bloque solo es analizado por herramientas de tipado estático
# como mypy, permitiéndonos tener type hints de modelos que se importan mutuamente.
if TYPE_CHECKING:
    from .client import ClientInBookingResponse
    from .class_session import ClassSessionInBookingResponse


# --- 1. Esquema Base ---
# Contiene los campos compartidos por la mayoría de los otros esquemas.
# Esto reduce la duplicidad de código y centraliza la definición común.
class BookingBase(BaseModel):
    """Esquema base para una reserva con campos comunes."""
    status: BookingStatus


# --- 2. Esquemas para Operaciones de Entrada (API Input) ---

class BookingCreate(BookingBase):
    """
    Esquema para la creación de una reserva desde la API.
    Define la lógica de negocio para crear una reserva a partir de una sesión específica
    o de un horario recurrente, pero no ambos.
    """
    class_session_id: Optional[uuid.UUID] = None
    class_schedule_id: Optional[uuid.UUID] = None

    # model_validator es el sucesor de root_validator en Pydantic V2.
    # Se ejecuta después de la validación de campos individuales (`mode='after'`).
    @model_validator(mode="after")
    def check_exactly_one_id_is_provided(self) -> 'BookingCreate':
        """
        Valida que se provea `class_session_id` o `class_schedule_id`, pero no ambos.
        Esta es una regla de negocio crítica para evitar ambigüedad al crear la reserva.
        """
        has_session_id = self.class_session_id is not None
        has_schedule_id = self.class_schedule_id is not None

        # Usamos XOR lógico (^) para expresar "uno o el otro, pero no ambos".
        # Es más conciso y claro que la condición original.
        if not (has_session_id ^ has_schedule_id):
            raise ValueError(
                "Debe proporcionar exclusivamente 'class_session_id' o 'class_schedule_id'."
            )
        return self


class BookingUpdate(BaseModel):
    """
    Esquema para la actualización de una reserva (PATCH).
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    status: Optional[BookingStatus] = None


# --- 3. Esquemas para Operaciones de Salida (API Response) ---

class Booking(BookingBase):
    """
    Esquema principal de respuesta para una reserva.
    Representa el objeto completo con sus relaciones anidadas, proporcionando
    una respuesta enriquecida al cliente.
    """
    id: uuid.UUID
    client_id: uuid.UUID
    class_session_id: uuid.UUID
    booking_date: datetime

    # Relaciones anidadas: Se cargan los objetos completos para dar más contexto.
    # Usamos forward references (strings) para evitar importaciones circulares.
    client: "ClientInBookingResponse"
    class_session: "ClassSessionInBookingResponse"

    # Configuración del modelo en Pydantic V2.
    # `from_attributes=True` (anteriormente orm_mode) permite que Pydantic
    # cree el esquema a partir de un modelo ORM (ej. SQLAlchemy), leyendo
    # los datos desde sus atributos en lugar de un diccionario.
    model_config = ConfigDict(from_attributes=True)


# --- 4. Esquemas para Respuestas Anidadas ---
# Estos esquemas son cruciales para evitar la recursión infinita en las respuestas JSON.
# Por ejemplo: Client -> [Bookings] -> Client -> [Bookings] ...

class BookingInClientResponse(BookingBase):
    """
    Representación simplificada de una reserva cuando se incluye dentro de un objeto `Client`.
    Se omite el objeto `client` completo para evitar la recursión.
    """
    id: uuid.UUID
    class_session_id: uuid.UUID
    booking_date: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingInClassSessionResponse(BookingBase):
    """
    Representación simplificada de una reserva cuando se incluye dentro de `ClassSession`.
    Se omite el objeto `class_session` completo para evitar la recursión.
    """
    id: uuid.UUID
    client_id: uuid.UUID
    booking_date: datetime

    model_config = ConfigDict(from_attributes=True)


# --- 5. Esquemas de Uso Interno ---

class BookingCreateInternal(BaseModel):
    """
    Esquema para la creación interna de una reserva en la capa de servicio/repositorio.
    No se expone a la API. Se utiliza después de que la lógica de negocio ha procesado
    `BookingCreate` y ha resuelto cuál es el `class_session_id` final.
    Contiene todos los campos necesarios y no opcionales para la inserción en la base de datos.
    """
    client_id: uuid.UUID
    class_session_id: uuid.UUID
    booking_date: datetime
    status: BookingStatus
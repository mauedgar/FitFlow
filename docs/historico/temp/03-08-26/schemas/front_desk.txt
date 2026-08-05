# app/schemas/front_desk.py
"""
Schemas operativos para el módulo Front Desk
--------------------------------------------
Estos esquemas NO reemplazan los esquemas base de GymClass, ClassSchedule,
ClassSession o Booking. Son "vistas" simplificadas para el flujo operativo
de mesa de entrada.

Se usan en endpoints como:
    • GET /front-desk/sessions/today
    • GET /front-desk/sessions/{id}/capacity
    • GET /front-desk/sessions/{id}/bookings
    • GET /front-desk/classes
    • GET /front-desk/schedule?class_id=...
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --------------------------------------------------------------------------- #
# CAPACIDAD DE SESIÓN
# --------------------------------------------------------------------------- #
class SessionCapacity(BaseModel):
    """
    Representa la capacidad disponible de una sesión:
        • capacidad total
        • reservas usadas
        • lugares disponibles
    """
    session_id: UUID
    capacity: int
    used: int
    available: int


# --------------------------------------------------------------------------- #
# SESIÓN DEL DÍA (vista operativa)
# --------------------------------------------------------------------------- #
class FrontDeskSessionView(BaseModel):
    """
    Vista simplificada de una sesión para el front desk.
    Incluye datos ya resueltos para evitar que el frontend navegue relaciones.
    """
    id: UUID
    starts_at: datetime
    ends_at: datetime
    status: str

    gym_class_name: str
    teacher_name: str

    capacity: int
    used: int
    available: int


# --------------------------------------------------------------------------- #
# RESERVA EN SESIÓN (vista operativa)
# --------------------------------------------------------------------------- #
class FrontDeskBookingView(BaseModel):
    """
    Vista simplificada de una reserva dentro de una sesión.
    """
    id: UUID
    client_name: str
    client_email: str
    status: str


# --------------------------------------------------------------------------- #
# CLASE ACTIVA (vista operativa)
# --------------------------------------------------------------------------- #
class FrontDeskClassView(BaseModel):
    """
    Vista simplificada de una clase activa para front desk.
    """
    id: UUID
    name: str
    difficulty: str
    activity_type: str

"""
Servicios para Booking (Sprint 6–7)
-----------------------------------
Incluye:
• Transformaciones ORM → Schemas públicos.
• Cálculo de disponibilidad.
• Validaciones de negocio.
• Validación de membresía vs allowed_plan.
• Helpers internos para repositorio/servicios.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import Booking, ClassSchedule, ClassSession, Membership

# --------------------------------------------------------------------------- #
# 1. Transformación automática: Booking → BookingPublic
# --------------------------------------------------------------------------- #

def to_booking_public(booking: Booking) -> schemas.BookingPublic:
    """
    Transforma un modelo ORM Booking en un esquema público BookingPublic.

    Campos expuestos:
        • id
        • status
        • starts_at / ends_at (desde la sesión)
        • gym_class_name (desde el horario → gym_class)
    """
    session: ClassSession = booking.class_session
    schedule: ClassSchedule = session.class_schedule
    gym_class = schedule.gym_class

    return schemas.BookingPublic(
        id=booking.id,
        status=booking.status,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        gym_class_name=gym_class.name,
    )


# --------------------------------------------------------------------------- #
# 2. Cálculo de disponibilidad
# --------------------------------------------------------------------------- #

def calculate_availability(session: ClassSession) -> int:
    """
    Calcula los lugares disponibles en una sesión.

    Fórmula:
        available = session.class_schedule.capacity - current_bookings_count
    """
    capacity = session.class_schedule.capacity
    used = session.current_bookings_count
    return max(capacity - used, 0)


def update_session_availability(session: ClassSession) -> ClassSession:
    """
    Actualiza los campos calculados de disponibilidad dentro del modelo ORM.
    """
    session.available_spots = calculate_availability(session)
    return session


# --------------------------------------------------------------------------- #
# 3. Validaciones de negocio
# --------------------------------------------------------------------------- #

def validate_booking_creation(session: ClassSession) -> None:
    """
    Valida si una reserva puede ser creada en una sesión.

    Reglas:
        • La sesión debe estar activa.
        • Debe haber lugares disponibles.
    """
    if session.status != schemas.ClassSessionStatus.scheduled:
        raise ValueError("La sesión no está activa o fue cancelada.")

    if calculate_availability(session) <= 0:
        raise ValueError("No hay lugares disponibles para esta sesión.")


# --------------------------------------------------------------------------- #
# 4. Validación de membresía vs allowed_plan
# --------------------------------------------------------------------------- #

def validate_membership_access(
    membership: Membership | None,
    schedule: ClassSchedule,
) -> None:
    """
    Valida si la membresía del cliente permite reservar este horario.

    Reglas:
        • Si el horario no tiene allowed_plan → acceso libre.
        • Si el cliente no tiene membresía → no puede reservar.
        • Si el plan del cliente no coincide con allowed_plan → prohibido.
        • Planes premium/personalized pueden acceder a todo.
    """
    allowed = schedule.allowed_plan

    # Horario sin restricciones
    if allowed is None:
        return

    # Cliente sin membresía
    if membership is None:
        raise ValueError("Necesitas una membresía activa para reservar esta clase.")

    # Plan del cliente
    client_plan = membership.plan

    # Premium y personalized pueden acceder a todo
    if client_plan in (schemas.MembershipPlan.premium, schemas.MembershipPlan.personalized):
        return

    # Restricción estricta
    if client_plan != allowed:
        raise ValueError(
            f"Tu membresía ({client_plan}) no permite reservar este horario "
            f"(requiere {allowed})."
        )


# --------------------------------------------------------------------------- #
# 5. Helpers internos para repositorio
# --------------------------------------------------------------------------- #

def to_booking_internal(
    client_id: str,
    session: ClassSession,
    status: schemas.BookingStatus,
) -> schemas.BookingCreateInternal:
    """
    Construye el esquema interno para insertar una reserva en la base de datos.
    """
    return schemas.BookingCreateInternal(
        client_id=client_id,
        class_session_id=session.id,
        created_at=datetime.now(tz=timezone.utc),
        status=status,
    )

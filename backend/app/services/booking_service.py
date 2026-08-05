"""Servicios para Booking.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Validaciones de negocio.
• Validación de membresía vs allowed_plan.
• Validaciones de sesión (activa, futura, capacidad).
• Validación de duplicación de reservas.
• Validación de overbooking.
• Helpers operativos para front desk y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app import schemas

if TYPE_CHECKING:
    from app.models import Booking, ClassSchedule, ClassSession, Membership


# --------------------------------------------------------------------------- #
# 1. Transformación automática: Booking → BookingPublic
# --------------------------------------------------------------------------- #

def to_booking_public(booking: Booking) -> schemas.BookingPublic:
    """Transforma un modelo ORM Booking en un esquema público BookingPublic."""
    session = booking.class_session
    schedule = session.class_schedule
    gym_class = schedule.gym_class

    return schemas.BookingPublic(
        id=booking.id, # pyright: ignore[reportArgumentType]
        status=booking.status, # pyright: ignore[reportArgumentType]
        starts_at=session.starts_at, # pyright: ignore[reportArgumentType]
        ends_at=session.ends_at, # pyright: ignore[reportArgumentType]
        gym_class_name=gym_class.name, # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Validaciones de sesión
# --------------------------------------------------------------------------- #

def validate_session_active(session: ClassSession) -> None:
    """La sesión debe estar activa."""
    if session.status != schemas.ClassSessionStatus.scheduled: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La sesión no está activa o fue cancelada."
        raise ValueError(msg)


def validate_session_future(session: ClassSession) -> None:
    """La sesión debe ser futura."""
    now = datetime.now(tz=timezone.utc)
    if session.starts_at <= now: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La sesión ya ocurrió."
        raise ValueError(msg)


def validate_session_capacity(session: ClassSession) -> None:
    """Debe haber cupos disponibles."""
    if session.available_spots <= 0:  # type: ignore[attr-defined]
        msg = "No hay lugares disponibles para esta sesión."
        raise ValueError(msg)


def validate_no_overbooking(session: ClassSession) -> None:
    """Evita condiciones de carrera cuando dos reservas llegan simultáneamente."""
    if session.current_bookings_count >= session.capacity_snapshot:  # type: ignore[attr-defined]
        msg = "La sesión se llenó mientras procesábamos tu reserva."
        raise ValueError(msg)


# --------------------------------------------------------------------------- #
# 3. Validación de duplicación de reservas
# --------------------------------------------------------------------------- #

def validate_no_duplicate_booking(client_id: str, session: ClassSession) -> None:
    """Evita que un cliente reserve dos veces la misma sesión."""
    for booking in session.bookings:
        if booking.client_id == client_id: # pyright: ignore[reportGeneralTypeIssues]
            msg = "Ya tienes una reserva para esta sesión."
            raise ValueError(msg)


# --------------------------------------------------------------------------- #
# 4. Validación de membresía vs allowed_plan
# --------------------------------------------------------------------------- #

def validate_membership_access(
    membership: Membership | None,
    schedule: ClassSchedule,
) -> None:
    """Valida si la membresía del cliente permite reservar este horario."""
    allowed = schedule.allowed_plan

    if allowed is None:
        return

    if membership is None:
        msg = "Necesitas una membresía activa para reservar esta clase."
        raise ValueError(msg)

    client_plan = membership.plan

    if client_plan in (schemas.MembershipPlan.premium, schemas.MembershipPlan.personalized):
        return

    if client_plan != allowed: # pyright: ignore[reportGeneralTypeIssues]
        msg_0 = f"Tu membresía ({client_plan}) no permite reservar este horario (requiere {allowed})."
        raise ValueError(
            msg_0,
        )


# --------------------------------------------------------------------------- #
# 5. Validación de límites (opcional pero útil)
# --------------------------------------------------------------------------- #

def validate_daily_limit(client_sessions_today: int, limit: int = 2) -> None:
    """Evita que un cliente reserve demasiadas sesiones en un mismo día."""
    if client_sessions_today >= limit:
        msg = "Has alcanzado el límite diario de reservas."
        raise ValueError(msg)


def validate_class_limit(client_class_count: int, limit: int = 4) -> None:
    """Evita que un cliente abuse de una misma clase."""
    if client_class_count >= limit:
        msg = "Has alcanzado el límite de reservas para esta clase."
        raise ValueError(msg)


# --------------------------------------------------------------------------- #
# 6. Helpers operativos
# --------------------------------------------------------------------------- #

def calculate_availability(session: ClassSession) -> int:
    """Calcula los lugares disponibles en una sesión."""
    capacity = session.capacity_snapshot
    used = session.current_bookings_count  # type: ignore[attr-defined]
    return max(capacity - used, 0) # pyright: ignore[reportReturnType]


def update_session_availability(session: ClassSession) -> ClassSession:
    """Actualiza los campos calculados de disponibilidad dentro del modelo ORM."""
    session.available_spots = calculate_availability(session)  # type: ignore[attr-defined]
    return session


# --------------------------------------------------------------------------- #
# 7. Construcción interna para repositorio
# --------------------------------------------------------------------------- #

def to_booking_internal(
    client_id: str,
    session: ClassSession,
    status: schemas.BookingStatus,
) -> schemas.BookingCreateInternal:
    """Construye el esquema interno para insertar una reserva en la base de datos."""
    return schemas.BookingCreateInternal(
        client_id=client_id, # pyright: ignore[reportArgumentType]
        class_session_id=session.id, # pyright: ignore[reportArgumentType]
        created_at=datetime.now(tz=timezone.utc),
        status=status,
    )

"""
Servicios para ClassSession (Sprint 6–7)
========================================
Incluye:
• Transformaciones ORM → Schemas públicos o compactos.
• Cálculo de disponibilidad.
• Validaciones de negocio.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app import schemas
from app.models import ClassSession

# --------------------------------------------------------------------------- #
# 1. Transformación automática: ClassSession → ClassSessionInResponse
# --------------------------------------------------------------------------- #

def to_class_session_response(session: ClassSession) -> schemas.ClassSessionInResponse:
    """
    Transforma un modelo ORM ClassSession en un esquema compacto.
    Usado dentro de ClassSchedule y GymClass.
    """
    return schemas.ClassSessionInResponse(
        id=session.id,
        class_schedule_id=session.class_schedule_id,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
        current_bookings_count=session.current_bookings_count,
        available_spots=calculate_availability(session),
    )


# --------------------------------------------------------------------------- #
# 2. Cálculo de disponibilidad
# --------------------------------------------------------------------------- #

def calculate_availability(session: ClassSession) -> int:
    """
    Calcula los lugares disponibles en una sesión.
    Fórmula:
        available = capacity_snapshot - current_bookings_count
    """
    capacity = session.capacity_snapshot
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

def validate_session_active(session: ClassSession) -> None:
    """
    Valida que la sesión esté activa y programada.
    """
    if session.status != schemas.ClassSessionStatus.scheduled:
        raise ValueError("La sesión no está activa o fue cancelada.")


def validate_session_future(session: ClassSession) -> None:
    """
    Valida que la sesión no haya ocurrido aún.
    """
    now = datetime.now(tz=timezone.utc)
    if session.starts_at <= now:
        raise ValueError("La sesión ya ocurrió.")


# --------------------------------------------------------------------------- #
# 4. Transformación completa con relaciones (opcional)
# --------------------------------------------------------------------------- #

def to_class_session_with_relations(session: ClassSession) -> schemas.ClassSessionWithRelations:
    """
    Devuelve una sesión con todas sus relaciones cargadas:
        • class_schedule
        • gym_class
        • teacher
        • bookings
    Ideal para:
        • /sessions/{id}
        • front desk
        • dashboards
    """
    schedule = session.class_schedule

    return schemas.ClassSessionWithRelations(
        id=session.id,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
        capacity_snapshot=session.capacity_snapshot,
        current_bookings_count=session.current_bookings_count,
        available_spots=calculate_availability(session),
        class_schedule=schedule,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher,
        bookings=session.bookings,
    )

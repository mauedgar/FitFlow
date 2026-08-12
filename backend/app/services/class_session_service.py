"""Servicios para ClassSession.

Incluye:
• Transformaciones ORM → Schemas públicos o compactos.
• Cálculo de disponibilidad.
• Validaciones de negocio.
• Estado emergente (live, upcoming, finished).
• Métricas de ocupación.
• Helpers operativos para front desk y dashboards.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.core.enums import ClassSessionStatus
from app.schemas.class_session import (
    ClassSessionInResponse,
    ClassSessionWithRelations,
)

if TYPE_CHECKING:
    from app.models import ClassSchedule, ClassSession


# --------------------------------------------------------------------------- #
# 1. Transformación automática: ClassSession → ClassSessionInResponse
# --------------------------------------------------------------------------- #

def to_class_session_response(session: ClassSession) -> ClassSessionInResponse:
    """Transforma un modelo ORM ClassSession en un esquema compacto."""
    return ClassSessionInResponse(
        id=session.id,  # pyright: ignore[reportArgumentType]
        class_schedule_id=session.class_schedule_id, # pyright: ignore[reportArgumentType]
        starts_at=session.starts_at, # pyright: ignore[reportArgumentType]
        ends_at=session.ends_at, # pyright: ignore[reportArgumentType]
        status=session.status, # pyright: ignore[reportArgumentType]
        current_bookings_count=session.current_bookings_count,  # type: ignore[attr-defined]
        available_spots=calculate_availability(session),
    )


# --------------------------------------------------------------------------- #
# 2. Cálculo de disponibilidad
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
# 3. Validaciones de negocio
# --------------------------------------------------------------------------- #

def validate_session_active(session: ClassSession) -> None:
    """Valida que la sesión esté activa y programada."""
    if session.status != ClassSessionStatus.scheduled: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La sesión no está activa o fue cancelada."
        raise ValueError(msg)


def validate_session_future(session: ClassSession) -> None:
    """Valida que la sesión no haya ocurrido aún."""
    now = datetime.now(tz=timezone.utc)
    if session.starts_at <= now: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La sesión ya ocurrió."
        raise ValueError(msg)


def validate_no_overbooking(session: ClassSession) -> None:
    """Evita condiciones de carrera cuando dos reservas llegan simultáneamente."""
    if session.current_bookings_count >= session.capacity_snapshot:  # type: ignore[attr-defined]
        msg = "La sesión se llenó mientras procesábamos tu reserva."
        raise ValueError(msg)


# --------------------------------------------------------------------------- #
# 4. Estado emergente de la sesión
# --------------------------------------------------------------------------- #

def is_session_live(session: ClassSession) -> bool:
    """Indica si la sesión está ocurriendo en este momento."""
    now = datetime.now(tz=timezone.utc)
    return session.starts_at <= now <= session.ends_at # pyright: ignore[reportReturnType]


def is_session_upcoming(session: ClassSession, minutes: int = 15) -> bool:
    """Indica si la sesión comienza dentro de X minutos."""
    now = datetime.now(tz=timezone.utc)
    delta = session.starts_at - now
    return 0 < delta.total_seconds() <= minutes * 60


def is_session_finished(session: ClassSession) -> bool:
    """Indica si la sesión ya terminó."""
    now = datetime.now(tz=timezone.utc)
    return session.ends_at < now # pyright: ignore[reportReturnType]


# --------------------------------------------------------------------------- #
# 5. Métricas de ocupación
# --------------------------------------------------------------------------- #

def get_session_occupancy(session: ClassSession) -> float:
    """Devuelve el porcentaje de ocupación de la sesión."""
    if session.capacity_snapshot == 0: # pyright: ignore[reportGeneralTypeIssues]
        return 0.0
    return session.current_bookings_count / session.capacity_snapshot  # type: ignore[attr-defined]


def is_session_almost_full(session: ClassSession, threshold: float = 0.8) -> bool:
    """Indica si la sesión está casi llena."""
    return get_session_occupancy(session) >= threshold


def is_session_empty(session: ClassSession) -> bool:
    """Indica si la sesión no tiene reservas."""
    return session.current_bookings_count == 0  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# 6. Sesiones futuras (acotadas a 1 semana)
# --------------------------------------------------------------------------- #

def get_future_sessions(schedule: ClassSchedule, days: int = 7) -> list[ClassSession]:
    """Devuelve las sesiones futuras del horario dentro de X días."""
    now = datetime.now(tz=timezone.utc)
    limit = now + timedelta(days=days)

    return [
        s for s in schedule.class_sessions
        if now < s.starts_at <= limit # pyright: ignore[reportGeneralTypeIssues]
    ]


# --------------------------------------------------------------------------- #
# 7. Transformación completa con relaciones
# --------------------------------------------------------------------------- #

def to_class_session_with_relations(session: ClassSession) -> ClassSessionWithRelations:
    """Devuelve una sesión con todas sus relaciones cargadas."""
    schedule = session.class_schedule

    return ClassSessionWithRelations(
        id=session.id,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
        capacity_snapshot=session.capacity_snapshot,
        current_bookings_count=session.current_bookings_count,  # type: ignore[attr-defined]
        available_spots=calculate_availability(session),
        class_schedule=schedule,
        gym_class=schedule.gym_class,
        teacher=schedule.teacher,
        bookings=session.bookings,
    )


"""Servicios para Booking (refactor Sprint 6.7).

Responsabilidades:
- Transformaciones ORM -> Pydantic (imports explícitos)
- Validaciones de negocio (lanzan excepciones de dominio)
- Helpers operativos (pure functions)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    BookingStatus,
    ClassSessionStatus,
    MembershipPlan,
    MembershipStatus,
)
from app.db.models import ClassSession

# Import explícito de schemas que usamos como tipos de retorno
from app.schemas.booking import BookingCreate, BookingCreateInternal, BookingPublic
from app.services.errors import BusinessValidationError, ConflictError

if TYPE_CHECKING:
    from app.db.models import Booking, ClassSchedule, ClassSession, Membership

# ruff: noqa: UP037
# --------------------------------------------------------------------------- #
# 1. Transformación automática: Booking -> BookingPublic
# --------------------------------------------------------------------------- #
def to_booking_public(booking: "Booking") -> BookingPublic:
    """Transforma un modelo ORM Booking en un esquema público BookingPublic."""
    session = booking.class_session
    schedule = session.class_schedule
    gym_class = schedule.gym_class

    return BookingPublic(
        id=booking.id,  # pyright: ignore[reportArgumentType]
        status=booking.status,  # pyright: ignore[reportArgumentType]
        starts_at=session.starts_at,  # pyright: ignore[reportArgumentType]
        ends_at=session.ends_at,  # pyright: ignore[reportArgumentType]
        gym_class_name=gym_class.name,  # pyright: ignore[reportArgumentType]
    )


# --------------------------------------------------------------------------- #
# 2. Validaciones de sesión (lanzan BusinessValidationError)
# --------------------------------------------------------------------------- #
def validate_session_active(session: "ClassSession") -> None:
    """La sesión debe estar activa."""
    if session.status not in {ClassSessionStatus.scheduled, ClassSessionStatus.open}:
        msg = "La sesión no está activa o fue cancelada."
        raise BusinessValidationError(msg)


def validate_session_future(session: "ClassSession") -> None:
    """La sesión debe ser futura."""
    now = datetime.now(tz=UTC)
    if session.starts_at <= now: # pyright: ignore[reportGeneralTypeIssues]
        msg = "La sesión ya ocurrió."
        raise BusinessValidationError(msg)


def validate_session_capacity(session: "ClassSession") -> None:
    """Debe haber cupos disponibles."""
    if session.available_spots <= 0:  # type: ignore[attr-defined]
        msg = "No hay lugares disponibles para esta sesión."
        raise BusinessValidationError(msg)


def validate_no_overbooking(session: "ClassSession") -> None:
    """Evita condiciones de carrera cuando dos reservas llegan simultáneamente."""
    if session.current_bookings_count >= session.capacity_snapshot:  # type: ignore[attr-defined]
        msg = "La sesión se llenó mientras procesábamos tu reserva."
        raise ConflictError(msg)


# --------------------------------------------------------------------------- #
# 3. Validación de duplicación de reservas
# --------------------------------------------------------------------------- #
def validate_no_duplicate_booking(client_id: str, session: "ClassSession") -> None:
    """Evita que un cliente reserve dos veces la misma sesión."""
    for booking in session.bookings:
        if booking.client_id == client_id:  # pyright: ignore[reportGeneralTypeIssues]
            msg = "Ya tienes una reserva para esta sesión."
            raise ConflictError(msg)


# --------------------------------------------------------------------------- #
# 4. Validación de membresía vs allowed_plan
# --------------------------------------------------------------------------- #
def validate_membership_access(membership: "Membership | None", schedule: "ClassSchedule") -> None:
    """Valida si la membresía del cliente permite reservar este horario."""
    allowed = schedule.allowed_plan
    if allowed is None:
        return

    if membership is None:
        msg = "Necesitas una membresía activa para reservar esta clase."
        raise BusinessValidationError(msg)

    client_plan = membership.plan

    # Planes premium/personalized siempre permiten

    if client_plan in (MembershipPlan.premium, MembershipPlan.personalized):
        return

    if client_plan != allowed: # pyright: ignore[reportGeneralTypeIssues]
        msg_0 = f"Tu membresía ({client_plan}) no permite reservar este horario (requiere {allowed})."
        raise BusinessValidationError(
            msg_0,
        )


# --------------------------------------------------------------------------- #
# 5. Validación de límites (opcional)
# --------------------------------------------------------------------------- #
def validate_daily_limit(client_sessions_today: int, limit: int = 2) -> None:  # noqa: D103
    if client_sessions_today >= limit:
        msg = "Has alcanzado el límite diario de reservas."
        raise BusinessValidationError(msg)


def validate_class_limit(client_class_count: int, limit: int = 4) -> None:  # noqa: D103
    if client_class_count >= limit:
        msg = "Has alcanzado el límite de reservas para esta clase."
        raise BusinessValidationError(msg)


# --------------------------------------------------------------------------- #
# 6. Helpers operativos (pure functions)
# --------------------------------------------------------------------------- #
def calculate_availability(session: "ClassSession") -> int:
    """Calcula los lugares disponibles en una sesión (pure)."""
    capacity = int(session.capacity_snapshot) # pyright: ignore[reportArgumentType]
    used = int(session.current_bookings_count)  # type: ignore[attr-defined]
    return max(capacity - used, 0)


def update_session_availability(session: "ClassSession") -> "ClassSession":
    """Actualiza los campos calculados de disponibilidad dentro del modelo ORM.

    Nota: esta función muta el objeto en memoria. Para evitar race conditions,
    la verificación final de cupo debe hacerse en el CRUD con una transacción.
    """
    session.available_spots = calculate_availability(session)  # type: ignore[attr-defined]
    return session


# --------------------------------------------------------------------------- #
# 7. Construcción interna para repositorio
# --------------------------------------------------------------------------- #
def to_booking_internal(client_id: str, session: "ClassSession", status: BookingStatus) -> BookingCreateInternal:
    """Construye el esquema interno para insertar una reserva en la base de datos."""
    return BookingCreateInternal(
        client_id=client_id,  # pyright: ignore[reportArgumentType]
        class_session_id=session.id,  # pyright: ignore[reportArgumentType]
        created_at=datetime.now(tz=UTC),
        status=status,
    )


def validate_booking_creation(session: "ClassSession", membership: "Membership | None") -> None:
    """Valida si una reserva puede ser creada en una sesión."""
    validate_session_active(session)
    validate_session_future(session)

    if session.available_spots <= 0:
        msg_0 = "No hay lugares disponibles para esta sesión."
        raise BusinessValidationError(msg_0)

    if membership is None or membership.status != MembershipStatus.active: # pyright: ignore[reportGeneralTypeIssues]
        msg_1 = "Necesitas una membresía activa para reservar."
        raise BusinessValidationError(msg_1)


async def resolve_booking_session(db: AsyncSession, booking_in: BookingCreate) -> ClassSession:
    """Resolve a request identifier to a future session that may be reserved."""
    options = [
        selectinload(ClassSession.class_schedule),
        selectinload(ClassSession.bookings),
    ]
    if booking_in.class_session_id is not None:
        stmt = select(ClassSession).where(ClassSession.id == booking_in.class_session_id)
    else:
        stmt = (
            select(ClassSession)
            .where(
                ClassSession.class_schedule_id == booking_in.class_schedule_id,
                ClassSession.starts_at > datetime.now(UTC),
                ClassSession.status.in_([ClassSessionStatus.scheduled, ClassSessionStatus.open]),
                ClassSession.active.is_(True),
                ClassSession.deleted_at.is_(None),
            )
            .order_by(ClassSession.starts_at)
            .limit(1)
        )
    session = (await db.execute(stmt.options(*options))).scalar_one_or_none()
    if session is None:
        msg = "No existe una sesión futura reservable para el identificador indicado."
        raise BusinessValidationError(msg)
    return session


def validate_booking_cancellation(booking: "Booking") -> None:
    """Keep booking history immutable after attendance is recorded."""
    if booking.status == BookingStatus.cancelled:
        msg = "La reserva ya fue cancelada."
        raise ConflictError(msg)
    if booking.status in {BookingStatus.attended, BookingStatus.no_show}:
        msg_0 = "Una reserva con asistencia registrada no puede cancelarse."
        raise BusinessValidationError(msg_0)

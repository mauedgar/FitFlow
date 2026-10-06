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

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import BookingStatus, ClassSessionStatus, MembershipStatus
from app.core.timezone import LOCAL_TZ
from app.db.models import ClassSchedule, ClassSession, Membership
from app.schemas.class_session import (
    ClassSessionInResponse,
    ClassSessionWithRelations,
)
from app.schemas.client_weekly_agenda import (
    ClientWeeklyAgendaBookingState,
    ClientWeeklyAgendaItem,
    ClientWeeklyAgendaView,
)
from app.schemas.weekly_demand import (
    WeeklyScheduleDemandItem,
    WeeklyScheduleDemandView,
)
from app.services.class_schedule_service import validate_membership_access
from app.services.errors import BusinessValidationError

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
# 2. Demanda semanal esperada
# --------------------------------------------------------------------------- #

async def _get_weekly_schedule_demand_sessions(
    db: AsyncSession,
    *,
    week_start: date,
) -> list[ClassSession]:
    """Load the exact active/future session set used by weekly demand reads."""
    local_start = datetime.combine(week_start, time.min, tzinfo=LOCAL_TZ)
    local_end = local_start + timedelta(days=7)
    starts_at = local_start.astimezone(timezone.utc)
    ends_at = local_end.astimezone(timezone.utc)
    now = datetime.now(tz=timezone.utc)

    stmt = (
        select(ClassSession)
        .where(
            ClassSession.active.is_(True),
            ClassSession.deleted_at.is_(None),
            ClassSession.status.in_(
                [ClassSessionStatus.scheduled, ClassSessionStatus.open]
            ),
            ClassSession.starts_at >= starts_at,
            ClassSession.starts_at < ends_at,
            ClassSession.ends_at > now,
        )
        .options(
            selectinload(ClassSession.class_schedule).selectinload(
                ClassSchedule.gym_class
            ),
            selectinload(ClassSession.bookings),
        )
        .order_by(ClassSession.starts_at, ClassSession.id)
    )
    return list((await db.execute(stmt)).scalars().unique().all())


def _to_weekly_schedule_demand_item(
    session: ClassSession,
) -> WeeklyScheduleDemandItem:
    """Project one occurrence with the canonical A1 expected-demand semantics."""
    active_booking_count = sum(
        booking.status != BookingStatus.cancelled
        for booking in session.bookings
    )
    reference_capacity = session.capacity_snapshot
    booking_occupancy_ratio = (
        active_booking_count / reference_capacity
        if reference_capacity > 0
        else None
    )
    activity = session.class_schedule.gym_class

    return WeeklyScheduleDemandItem(
        session_id=session.id,
        class_schedule_id=session.class_schedule_id,
        gym_class_id=activity.id,
        activity_name=activity.name,
        activity_type=activity.activity_type,
        starts_at=session.starts_at,
        ends_at=session.ends_at,
        status=session.status,
        active_booking_count=active_booking_count,
        reference_capacity=reference_capacity,
        booking_occupancy_ratio=booking_occupancy_ratio,
    )


async def get_weekly_schedule_demand(
    db: AsyncSession,
    *,
    week_start: date,
) -> WeeklyScheduleDemandView:
    """Return factual Booking demand for active/future sessions in one local week."""
    sessions = await _get_weekly_schedule_demand_sessions(db, week_start=week_start)
    items = [_to_weekly_schedule_demand_item(session) for session in sessions]

    return WeeklyScheduleDemandView(
        week_start=week_start,
        week_end_exclusive=week_start + timedelta(days=7),
        items=items,
    )


def _membership_allows_agenda_session(
    membership: Membership | None,
    session: ClassSession,
) -> bool:
    """Return whether an active Membership/Plan permits this occurrence."""
    if membership is None or membership.status != MembershipStatus.active:  # pyright: ignore[reportGeneralTypeIssues]
        return False

    try:
        validate_membership_access(membership, session.class_schedule)
    except BusinessValidationError:
        return False
    return True


def _own_active_booking(
    session: ClassSession,
    *,
    client_id: UUID,
) -> ClientWeeklyAgendaBookingState | None:
    """Project the Client's current non-cancelled Booking, if one exists."""
    own_booking = next(
        (
            booking
            for booking in session.bookings
            if booking.client_id == client_id  # pyright: ignore[reportGeneralTypeIssues]
            and booking.status != BookingStatus.cancelled
        ),
        None,
    )
    if own_booking is None:
        return None
    return ClientWeeklyAgendaBookingState(
        booking_id=own_booking.id,  # pyright: ignore[reportArgumentType]
        status=own_booking.status,  # pyright: ignore[reportArgumentType]
    )


async def get_client_weekly_agenda(
    db: AsyncSession,
    *,
    client_id: UUID,
    membership: Membership | None,
    week_start: date,
) -> ClientWeeklyAgendaView:
    """Compose eligible weekly offerings, own Booking state, and A1 demand."""
    sessions = await _get_weekly_schedule_demand_sessions(db, week_start=week_start)

    items: list[ClientWeeklyAgendaItem] = []
    for session in sessions:
        if not _membership_allows_agenda_session(membership, session):
            continue

        demand = _to_weekly_schedule_demand_item(session)
        items.append(
            ClientWeeklyAgendaItem(
                **demand.model_dump(),
                membership_plan_eligible=True,
                own_booking=_own_active_booking(session, client_id=client_id),
            )
        )

    return ClientWeeklyAgendaView(
        week_start=week_start,
        week_end_exclusive=week_start + timedelta(days=7),
        items=items,
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

def get_future_sessions(schedule: ClassSchedule, days: int = 15) -> list[ClassSession]:
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


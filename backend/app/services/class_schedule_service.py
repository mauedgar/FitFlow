# app/services/class_schedule_service.py
"""Servicios para ClassSchedule.

Incluye:
• Transformaciones ORM → Schemas públicos.
• Validaciones de negocio.
• Estado emergente del horario.
• Métricas operativas.
• Sesiones del día y de la semana.
• Próxima sesión futura.
• Helpers para front desk y dashboards.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from dateutil.rrule import rrulestr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AllowedPlan, ClassSessionStatus, MembershipPlan
from app.core.timezone import LOCAL_TZ
from app.crud.crud_class_schedule import (
    class_schedule as crud_class_schedule,
)
from app.crud.crud_class_session import class_session as crud_class_session
from app.db.models.membership import Membership  # noqa: TC001
from app.db.session import get_async_session
from app.schemas.class_schedule import (
    ClassSchedulePublic,
    ClassScheduleWithNextSession,
    NextSessionInfo,
)
from app.schemas.class_session import ClassSessionPublic
from app.services import errors as svc_errors

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.class_schedule import ClassSchedule
    from app.db.models.class_session import ClassSession
    from app.schemas.user import UserPublic

# ruff: noqa: UP037
# -------------------------
# Helpers internos
# -------------------------
async def _get_db_session(db: "AsyncSession | None") -> "AsyncSession":
    """Obtener AsyncSession si no fue pasada (avanza el generator)."""
    if db is not None:
        return db
    gen = get_async_session()
    return  await gen.__anext__()  # type: ignore[attr-defined]


def _now_utc() -> datetime:
    """Hora actual en UTC (tz-aware)."""
    return datetime.now(tz=timezone.utc)


def _to_local(dt: datetime) -> datetime:
    """Convierte datetime aware a LOCAL_TZ."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ)


def _to_utc(dt: datetime) -> datetime:
    """Convierte datetime aware a UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(timezone.utc)


def _build_rrule(schedule: "ClassSchedule"):
    """Build the canonical RRULE anchored at the schedule's local start."""
    dtstart = datetime.combine(schedule.start_date, schedule.start_time, tzinfo=LOCAL_TZ)
    try:
        return rrulestr(schedule.rrule, dtstart=dtstart)
    except (TypeError, ValueError) as err:
        msg = "RRULE inválido en schedule."
        raise svc_errors.BusinessValidationError(msg) from err


def _occurrences_between(
    rule_obj: object,
    window_start: date,
    window_end: date,
    schedule_start_time: time,
) -> list[datetime]:
    """Devuelve ocurrencias (LOCAL_TZ tz-aware) del rule entre window_start y window_end.

    Asegura que la hora de cada ocurrencia coincida con schedule_start_time.
    """
    start_dt = datetime.combine(window_start, datetime.min.time()).replace(tzinfo=LOCAL_TZ)
    end_dt = datetime.combine(window_end, datetime.max.time()).replace(tzinfo=LOCAL_TZ)
    occs = list(rule_obj.between(start_dt, end_dt, inc=True))  # type: ignore[attr-defined]
    normalized: list[datetime] = []
    for occ_dt in occs:
        occ_local = occ_dt if occ_dt.tzinfo is not None else occ_dt.replace(tzinfo=LOCAL_TZ)
        occ_local = occ_local.astimezone(LOCAL_TZ)
        occ_local = occ_local.replace(
            hour=schedule_start_time.hour,
            minute=schedule_start_time.minute,
            second=schedule_start_time.second,
            microsecond=0,
        )
        normalized.append(occ_local)
    return normalized


# -------------------------
# 1. Transformaciones
# -------------------------
def to_class_schedule_public(schedule: "ClassSchedule") -> ClassSchedulePublic:
    """Transforma ORM ClassSchedule a ClassSchedulePublic (esquema)."""
    return ClassSchedulePublic.model_validate(
        {
            "id": schedule.id,
            "gym_class": schedule.gym_class,
            "teacher": schedule.teacher,
            "rrule": schedule.rrule,
            "start_time": schedule.start_time,
            "duration_minutes": schedule.duration_minutes,
            "capacity": schedule.capacity,
            "start_date": schedule.start_date,
            "end_date": schedule.end_date,
            "allowed_plan": schedule.allowed_plan,
        },
    )


# -------------------------
# 2. Validaciones de negocio
# -------------------------
def validate_schedule_active(schedule: "ClassSchedule") -> None:
    """Valida que el horario esté dentro de su rango de fechas."""
    now = _now_utc().date()
    if schedule.start_date and now < schedule.start_date:  # pyright: ignore[reportGeneralTypeIssues]
        msg = "El horario aún no está activo."
        raise svc_errors.BusinessValidationError(msg)
    if schedule.end_date and now > schedule.end_date: # pyright: ignore[reportGeneralTypeIssues]
        msg = "El horario ya no está activo."
        raise svc_errors.BusinessValidationError(msg)


def validate_schedule_integrity(schedule: "ClassSchedule") -> None:
    """Valida integridad mínima del schedule (clase, profesor, capacity)."""
    if schedule.gym_class is None:
        msg = "El horario no tiene clase asignada."
        raise svc_errors.BusinessValidationError(msg)
    if schedule.teacher is None:
        msg = "El horario no tiene profesor asignado."
        raise svc_errors.BusinessValidationError(msg)
    if schedule.capacity is None or int(schedule.capacity) < 1: # pyright: ignore[reportArgumentType]
        msg_0 = "Capacity inválida en el schedule."
        raise svc_errors.BusinessValidationError(msg_0)

def validate_membership_access(
    membership: "Membership | None",
    class_schedule: "ClassSchedule",
) -> None:
    """Valida que la membresía permita acceder al horario de una clase.

    La validación asume que el estado de la membresía ya fue comprobado
    previamente por ``validate_booking_creation()``.

    El acceso se determina según una jerarquía de planes:

    - ``gym_only``: permite horarios restringidos a ``gym_only``.
    - ``classes``: permite clases cuyo ``allowed_plan`` sea ``classes``.
    - ``premium``: permite ``gym_only``, ``classes`` y ``premium``.
    - ``personalized``: permite ``gym_only``, ``classes``, ``premium`` y
      ``personalized``.

    Si el horario no define ``allowed_plan`` (``None``), se considera
    de acceso libre para cualquier membresía activa.

    Args:
        membership: Membresía del cliente que intenta reservar.
        class_schedule: Horario de la clase que se desea reservar.

    Raises:
        BusinessValidationError: Si la membresía no tiene un plan válido
            para acceder al horario.

    """
    if membership is None:
        msg = "Necesitas una membresía para acceder a esta clase."
        raise svc_errors.BusinessValidationError(msg)

    allowed_plan = class_schedule.allowed_plan

    # None significa que el horario no tiene restricción de plan.
    if allowed_plan is None:
        return

    membership_plan = membership.plan

    allowed_plans_by_membership = {
        MembershipPlan.gym_only: {
            AllowedPlan.gym_only,
        },
        MembershipPlan.classes: {
            AllowedPlan.classes,
        },
        MembershipPlan.premium: {
            AllowedPlan.gym_only,
            AllowedPlan.classes,
            AllowedPlan.premium,
        },
        MembershipPlan.personalized: {
            AllowedPlan.gym_only,
            AllowedPlan.classes,
            AllowedPlan.premium,
            AllowedPlan.personalized,
        },
    }

    allowed_plans = allowed_plans_by_membership.get(
        membership_plan,
        set(),
    )

    if allowed_plan not in allowed_plans:
        msg = (
            "Tu membresía no permite reservar esta clase. "
            f"Se requiere un plan '{allowed_plan.value}'."
        )
        raise svc_errors.BusinessValidationError(msg)



# -------------------------
# 3. Estado emergente y consultas
# -------------------------
def has_sessions_today(schedule: "ClassSchedule") -> bool:
    """Indica si el schedule tiene sesiones hoy (comparando en UTC)."""
    today = _now_utc().date()
    return any(getattr(s, "starts_at", None) and s.starts_at.date() == today for s in schedule.class_sessions or [])


def has_future_sessions(schedule: "ClassSchedule") -> bool:
    """Indica si el schedule tiene sesiones futuras."""
    now = _now_utc()
    return any(getattr(s, "starts_at", None) and s.starts_at > now for s in schedule.class_sessions or [])


def get_sessions_today(schedule: "ClassSchedule") -> list["ClassSession"]:
    """Devuelve las sesiones del día para este schedule (UTC comparison)."""
    today = _now_utc().date()
    return [s for s in (schedule.class_sessions or []) if getattr(s, "starts_at", None) and s.starts_at.date() == today]


def get_sessions_this_week(schedule: "ClassSchedule") -> list["ClassSession"]:
    """Devuelve las sesiones de los próximos 7 días desde ahora."""
    now = _now_utc()
    limit = now + timedelta(days=7)
    sessions = schedule.class_sessions or []
    return [
        s for s in sessions
        if getattr(s, "starts_at", None) is not None and now < s.starts_at <= limit # pyright: ignore[reportGeneralTypeIssues]
    ]

# -------------------------
# 4. Métricas
# -------------------------
def get_schedule_occupancy(schedule: "ClassSchedule") -> float:
    """Devuelve la ocupación promedio del schedule (0.0..1.0)."""
    sessions = schedule.class_sessions or []
    if not sessions:
        return 0.0
    total_bookings = sum(getattr(s, "current_bookings_count", 0) or 0 for s in sessions)
    total_capacity = sum((getattr(s, "capacity_snapshot", {}) or {}).get("capacity", 0) for s in sessions)
    if total_capacity == 0:
        return 0.0
    return float(total_bookings) / float(total_capacity)


def get_schedule_next_session(schedule: "ClassSchedule") -> NextSessionInfo | None:
    """Devuelve la próxima sesión futura del schedule como NextSessionInfo o None."""
    now = _now_utc()
    sessions = schedule.class_sessions or []
    future_sessions = [
        s for s in sessions
        if getattr(s, "starts_at", None) is not None and s.starts_at > now # pyright: ignore[reportGeneralTypeIssues]
    ]
    if not future_sessions:
        return None

    next_session = min(future_sessions, key=lambda s: s.starts_at)
    available = (getattr(next_session, "capacity_snapshot", {}) or {}).get("capacity", 0) - (getattr(next_session, "current_bookings_count", 0) or 0)
    return NextSessionInfo.model_validate(
        {
            "session_id": next_session.id,
            "starts_at": next_session.starts_at,
            "available_spots": max(0, int(available)),
            "current_bookings_count": int(getattr(next_session, "current_bookings_count", 0) or 0),
        },
    )


def to_class_schedule_with_next_session(schedule: "ClassSchedule") -> ClassScheduleWithNextSession:
    """Transforma schedule a ClassScheduleWithNextSession (incluye next_session)."""
    public = to_class_schedule_public(schedule)
    next_info = get_schedule_next_session(schedule)
    data = public.model_dump()
    data["next_session"] = next_info
    return ClassScheduleWithNextSession.model_validate(data)


# -------------------------
# 5. Generación de sesiones (orquestador)
# -------------------------
async def generate_sessions_for_schedule(
    *,
    schedule_id: UUID,
    window_start: date,
    window_end: date,
    db: AsyncSession,
) -> list[ClassSessionPublic]:
    """Crea las sesiones futuras faltantes de un ClassSchedule en una ventana."""
    schedule = await crud_class_schedule.get_for_session_generation(
        db,
        schedule_id=schedule_id,
    )
    if schedule is None:
        msg = "ClassSchedule no encontrado."
        raise svc_errors.NotFoundError(msg)

    validate_schedule_integrity(schedule)

    effective_start = max(window_start, schedule.start_date)
    effective_end = (
        min(window_end, schedule.end_date)
        if schedule.end_date is not None
        else window_end
    )

    if effective_end < effective_start:
        return []

    window_starts_at = _to_utc(
        datetime.combine(effective_start, time.min, tzinfo=LOCAL_TZ),
    )
    window_ends_at = _to_utc(
        datetime.combine(effective_end, time.max, tzinfo=LOCAL_TZ),
    )

    existing_starts = await crud_class_session.get_starts_for_schedule_in_window(
        db,
        schedule_id=schedule.id,
        starts_at=window_starts_at,
        ends_at=window_ends_at,
    )

    occurrences = _occurrences_between(
        _build_rrule(schedule),
        effective_start,
        effective_end,
        schedule.start_time,
    )

    now = _now_utc()
    sessions_data: list[dict[str, object]] = []

    for local_start in occurrences:
        starts_at = _to_utc(local_start)

        if starts_at <= now or starts_at in existing_starts:
            continue

        ends_at = starts_at + timedelta(minutes=schedule.duration_minutes)

        has_conflict = await crud_class_session.teacher_has_conflict(
            db,
            teacher_id=schedule.teacher_id,
            excluded_schedule_id=schedule.id,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        if has_conflict:
            msg = "Solapamiento detectado para el profesor."
            raise svc_errors.BusinessValidationError(
                msg,
            )

        sessions_data.append(
            {
                "class_schedule_id": schedule.id,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "capacity_snapshot": schedule.capacity,
                "status": ClassSessionStatus.scheduled,
            },
        )

    created = await crud_class_session.create_many(
        db,
        sessions_data=sessions_data,
    )

    return [
        ClassSessionPublic.model_validate(
            {
                "id": session.id,
                "class_schedule_id": session.class_schedule_id,
                "starts_at": session.starts_at,
                "ends_at": session.ends_at,
                "capacity_snapshot": session.capacity_snapshot,
                "status": session.status,
                "current_bookings_count": 0,
                "available_spots": session.capacity_snapshot,
            },
        )
        for session in created
    ]

# -------------------------
# 6. Helpers operativos
# -------------------------
def get_sessions_for_day(schedule: "ClassSchedule", target_date: date) -> list[ClassSession]:
    """Devuelve sesiones del schedule para una fecha específica (UTC comparison)."""
    return [s for s in (schedule.class_sessions or []) if getattr(s, "starts_at", None) and s.starts_at.date() == target_date]


def get_next_session(schedule: "ClassSchedule") -> NextSessionInfo | None:
    """Alias que devuelve la próxima sesión (NextSessionInfo) si existe."""
    return get_schedule_next_session(schedule)

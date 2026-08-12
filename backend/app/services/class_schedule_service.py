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

from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule, rruleset, rrulestr
from sqlalchemy.ext.asyncio import AsyncSession  # top-level import

from app.core.timezone import LOCAL_TZ
from app.crud.crud_class_schedule import class_schedule as class_schedule_crud
from app.crud.crud_class_session import class_session as class_session_crud
from app.db.session import get_async_session
from app.schemas.class_schedule import (
    ClassSchedulePublic,
    ClassScheduleWithNextSession,
    NextSessionInfo,
)
from app.schemas.class_session import ClassSessionCreate, ClassSessionPublic
from app.services import errors as svc_errors
from app.core.enums import AllowedPlan, MembershipPlan
from app.models.membership import Membership  # noqa: TC001

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.class_schedule import ClassSchedule
    from app.models.class_session import ClassSession
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


def _map_days_to_rrule_byweekday(days: list[int]) -> list:
    """Mapea lista 0..6 a constantes dateutil (MO..SU)."""
    mapping = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA, 6: SU}
    return [mapping[d] for d in days if d in mapping]


def _build_rrule(schedule: "ClassSchedule", window_start: date, window_end: date)->rrule|rruleset:  # noqa: ARG001
    """Construye rrule desde schedule.rrule preferente; days_of_week fallback."""
    raw = getattr(schedule, "rrule", None)
    dtstart = datetime.combine(schedule.start_date, schedule.start_time).replace(tzinfo=LOCAL_TZ) # pyright: ignore[reportArgumentType]
    if raw:
        try:
            return rrulestr(raw, dtstart=dtstart)
        except Exception as err:
            msg = "RRULE inválido en schedule."
            raise svc_errors.BusinessValidationError(msg) from err

    days = getattr(schedule, "days_of_week", []) or []
    if not days:
        return rrule(freq=WEEKLY, count=1, dtstart=dtstart)

    byweekday = _map_days_to_rrule_byweekday(days)
    dtstart_window = datetime.combine(window_start, schedule.start_time).replace(tzinfo=LOCAL_TZ) # pyright: ignore[reportArgumentType]
    return rrule(freq=WEEKLY, byweekday=byweekday, dtstart=dtstart_window)

    # Fallback: days_of_week  # noqa: ERA001
    days = getattr(schedule, "days_of_week", []) or []
    if not days:
        # única ocurrencia en start_date
        return rrule(freq=WEEKLY, count=1, dtstart=dtstart)

    byweekday = _map_days_to_rrule_byweekday(days)
    # dtstart: usar window_start con la hora del schedule para generar desde la ventana
    dtstart_window = datetime.combine(window_start, schedule.start_time).replace(tzinfo=LOCAL_TZ) # pyright: ignore[reportArgumentType]
    return rrule(freq=WEEKLY, byweekday=byweekday, dtstart=dtstart_window)


def _occurrences_between(
    rule_obj: "rrule",
    window_start: date,
    window_end: date,
    schedule_start_time: time,
) -> list[datetime]:
    """Devuelve ocurrencias (LOCAL_TZ tz-aware) del rule entre window_start y window_end.

    Asegura que la hora de cada ocurrencia coincida con schedule_start_time.
    """
    start_dt = datetime.combine(window_start, datetime.min.time()).replace(tzinfo=LOCAL_TZ)
    end_dt = datetime.combine(window_end, datetime.max.time()).replace(tzinfo=LOCAL_TZ)
    occs = list(rule_obj.between(start_dt, end_dt, inc=True))
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
            "rrule": getattr(schedule, "rrule", None),
            "days_of_week": getattr(schedule, "days_of_week", None),
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
    if schedule.capacity is None or int(schedule.capacity) < 0: # pyright: ignore[reportArgumentType]
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

    - ``gym_only``: no permite acceder a clases.
    - ``classes``: permite clases cuyo ``allowed_plan`` sea ``classes``.
    - ``premium``: permite clases ``classes`` y ``premium``.
    - ``personalized``: permite clases ``classes``, ``premium`` y
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
        MembershipPlan.gym_only: set(),
        MembershipPlan.classes: {
            AllowedPlan.classes,
        },
        MembershipPlan.premium: {
            AllowedPlan.classes,
            AllowedPlan.premium,
        },
        MembershipPlan.personalized: {
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
async def generate_sessions_for_schedule(  # noqa: C901
    schedule_id: str,
    window_start: date,
    window_end: date,
    created_by: "UserPublic",
    db: "AsyncSession | None" = None,
) -> list[ClassSessionPublic]:
    """Genera (o asegura existencia) de ClassSession para el schedule en la ventana [window_start, window_end].
    - Usa schedule.rrule si está presente; si no, usa days_of_week como fallback.
    - Valida solapamiento de teacher antes de crear sesiones.
    - Copia capacity a capacity_snapshot en cada ClassSession.
    """  # noqa: D205
    db = await _get_db_session(db)
    sched = await class_schedule_crud.get(db, obj_id=UUID(schedule_id), include_relations=True)  # type: ignore[name-defined]
    if not sched:
        msg = "ClassSchedule no encontrado."
        raise svc_errors.NotFoundError(msg)

    # Validaciones básicas
    validate_schedule_integrity(sched)

    # Construir rrule y obtener ocurrencias en LOCAL_TZ
    rule_obj = _build_rrule(sched, window_start, window_end)
    occs_local = _occurrences_between(rule_obj, window_start, window_end, sched.start_time) # pyright: ignore[reportArgumentType]

    created_sessions: list[ClassSessionPublic] = []

    # Cargar sesiones existentes del teacher en ventana para validar solapamientos
    # Usamos CRUD para obtener schedules del mismo teacher en ventana y sus sessions
    teacher_schedules = await class_schedule_crud.get_multi_filtered(
        db,
        teacher_id=sched.teacher_id, # pyright: ignore[reportArgumentType]
        date_from=window_start,
        date_to=window_end,
        include_relations=True,
    )
    existing_sessions: list = []
    for s in teacher_schedules:
        sessions = getattr(s, "class_sessions", []) or []
        # filtrar y extender
        existing_sessions.extend([cs for cs in sessions if getattr(cs, "starts_at", None) is not None])

    def _overlaps(a_start: datetime, a_dur: int, b_start: datetime, b_dur: int) -> bool:
        a0 = a_start
        a1 = a_start + timedelta(minutes=a_dur)
        b0 = b_start
        b1 = b_start + timedelta(minutes=b_dur)
        return not (a1 <= b0 or b1 <= a0)

    for occ_local in occs_local:
        # Normalizar a UTC para persistir
        occ_utc = _to_utc(occ_local)
        # Validar solapamiento con existing_sessions
        for ex in existing_sessions:
            ex_start = getattr(ex, "starts_at", None)
            ex_dur = getattr(ex, "duration_minutes", sched.duration_minutes)
            if ex_start is None:
                continue
            # Asegurar ex_start es tz-aware UTC
            if ex_start.tzinfo is None:
                ex_start = ex_start.replace(tzinfo=timezone.utc)
            if _overlaps(occ_utc, sched.duration_minutes, ex_start, ex_dur): # pyright: ignore[reportArgumentType]
                msg_0 = "Solapamiento detectado para el profesor en la ventana solicitada."
                raise svc_errors.BusinessValidationError(msg_0)

        # Preparar payload mínimo para crear session
        cs_payload = {
            "class_schedule_id": str(sched.id),
            "starts_at": occ_utc,
            "duration_minutes": int(sched.duration_minutes), # pyright: ignore[reportArgumentType]
            "capacity_snapshot": {"capacity": int(sched.capacity)}, # pyright: ignore[reportArgumentType]
            "status": "scheduled",
        }

        # Intentar get_or_create si el CRUD lo soporta
        try:
            created_obj, created_flag = await class_session_crud.get_or_create(  # noqa: RUF059
                db,
                defaults={
                    "duration_minutes": sched.duration_minutes,
                    "capacity_snapshot": {"capacity": int(sched.capacity)}, # pyright: ignore[reportArgumentType]
                    "status": "scheduled",
                },
                class_schedule_id=sched.id,
                starts_at=occ_utc,
            )
            cs_obj = created_obj
        except AttributeError:
            # Fallback: usar create_with_capacity_snapshot si get_or_create no existe
            try:
                # class_session_crud.create_with_capacity_snapshot espera un schema; adaptamos si es necesario
                cs_payload = {
                    "class_schedule_id": str(sched.id),
                    "starts_at": occ_utc.isoformat(),
                    "duration_minutes": sched.duration_minutes,
                    "capacity_snapshot": {"capacity": int(sched.capacity)}, # pyright: ignore[reportArgumentType]
                    "status": "scheduled",
                }

                cs_schema = ClassSessionCreate.model_validate(cs_payload)  # pydantic v2
                cs_obj = await class_session_crud.create_with_capacity_snapshot(
                    db,
                    obj_in=cs_schema,
                    created_by=getattr(created_by, "id", None),
                )
            except Exception as err:
                msg_1 = "Error al crear ClassSession."
                raise svc_errors.ExternalServiceError(msg_1) from err

        # Convertir a schema público (si ya es ORM, ClassSessionPublic.model_validate lo acepta)
        created_sessions.append(ClassSessionPublic.model_validate(cs_obj))

    return created_sessions


# -------------------------
# 6. Helpers operativos
# -------------------------
def get_sessions_for_day(schedule: "ClassSchedule", target_date: date) -> list[ClassSession]:
    """Devuelve sesiones del schedule para una fecha específica (UTC comparison)."""
    return [s for s in (schedule.class_sessions or []) if getattr(s, "starts_at", None) and s.starts_at.date() == target_date]


def get_next_session(schedule: "ClassSchedule") -> NextSessionInfo | None:
    """Alias que devuelve la próxima sesión (NextSessionInfo) si existe."""
    return get_schedule_next_session(schedule)

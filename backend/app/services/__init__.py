# app/services/__init__.py
"""Paquete de servicios internos de la aplicación."""
# ruff: noqa: F401
from app.services.booking_service import (
    to_booking_internal,
    to_booking_public,
    validate_booking_creation,
    validate_class_limit,
    validate_daily_limit,
    validate_membership_access,
    validate_no_duplicate_booking,
    validate_no_overbooking,
    validate_session_active,
    validate_session_capacity,
    validate_session_future,
)
from app.services.class_schedule_service import (
    get_next_session,
    get_schedule_next_session,
    get_schedule_occupancy,
    get_sessions_this_week,
    has_future_sessions,
    has_sessions_today,
    to_class_schedule_public,
    to_class_schedule_with_next_session,
    validate_schedule_integrity,
)
from app.services.class_session_service import (
    calculate_availability,
    get_future_sessions,
    get_session_occupancy,
    is_session_almost_full,
    is_session_empty,
    is_session_finished,
    is_session_live,
    is_session_upcoming,
    to_class_session_response,
    to_class_session_with_relations,
    update_session_availability,
)
from app.services.client_service import (
    get_client_active_bookings,
    get_client_bookings_this_week,
    get_client_bookings_today,
    get_client_daily_activity,
    get_client_past_bookings,
    get_client_total_bookings,
    get_client_upcoming_bookings,
    get_client_weekly_activity,
    to_client_public,
    to_client_with_activity,
    to_client_with_bookings,
    to_client_with_membership,
    to_client_with_stats,
    unlink_user_profile,
)
from app.services.front_desk_service import (
    cancel_session,
    get_active_classes,
    get_schedule_by_class,
    get_session_bookings,
    get_session_capacity,
    get_sessions_today,
    to_frontdesk_session_view,
)
from app.services.gym_class_service import (
    to_gym_class_public,
    to_gym_class_with_schedules,
)
from app.services.membership_service import (
    is_membership_expiring_soon,
    is_membership_valid_for_booking,
    to_membership_public,
    to_membership_with_client,
    to_membership_with_stats,
    validate_membership_active,
    validate_membership_not_expired,
)
from app.services.teacher_service import (
    get_teacher_average_occupancy,
    get_teacher_future_sessions_count,
    get_teacher_total_classes,
    to_teacher_public,
    to_teacher_with_metrics,
    to_teacher_with_next_session,
    to_teacher_with_schedules,
    validate_teacher_active,
)
from app.services.user_service import (
    to_user_public,
    to_user_with_profile,
    to_user_with_stats,
)

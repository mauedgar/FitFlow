# ruff: noqa: F401
"""Model package for FitFlow backend."""

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

from backend.app.core.enums import (
    ActivityType,
    AllowedPlan,
    BookingStatus,
    ClassSessionStatus,
    DifficultyLevel,
    MembershipPlan,
    MembershipStatus,
    UserRole,
)

# --------------------------------------------------------------------------- #
# Base Schemas
# --------------------------------------------------------------------------- #
from .base import (
    IDSchema,
    OperationalSchema,
    PublicIDSchema,
    PublicTimestampSchema,
    SoftDeleteSchema,
    TimestampSchema,
)

# --------------------------------------------------------------------------- #
# Booking
# --------------------------------------------------------------------------- #
from .booking import (
    Booking,
    BookingBase,
    BookingCreate,
    BookingCreateInternal,
    BookingInClassSessionResponse,
    BookingInClientResponse,
    BookingPublic,
    BookingUpdate,
    BookingWithClient,
    BookingWithSession,
)

# --------------------------------------------------------------------------- #
# ClassSchedule
# --------------------------------------------------------------------------- #
from .class_schedule import (
    ClassSchedule,
    ClassScheduleBase,
    ClassScheduleCreate,
    ClassScheduleInClassSessionResponse,
    ClassSchedulePublic,
    ClassScheduleUpdate,
    ClassScheduleWithNextSession,
    NextSessionInfo,
)

# --------------------------------------------------------------------------- #
# ClassSession
# --------------------------------------------------------------------------- #
from .class_session import (
    ClassSession,
    ClassSessionBase,
    ClassSessionCreate,
    ClassSessionInBookingResponse,
    ClassSessionInResponse,
    ClassSessionPublic,
    ClassSessionUpdate,
    ClassSessionWithNext,
    ClassSessionWithSchedule,
)

# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
from .client import (
    Client,
    ClientBase,
    ClientCreate,
    ClientInBookingResponse,
    ClientPublic,
    ClientUpdate,
    ClientWithActivity,
    ClientWithBookings,
    ClientWithMembership,
    ClientWithStats,
)

# --------------------------------------------------------------------------- #
# Front Desk
# --------------------------------------------------------------------------- #
from .front_desk import (
    FrontDeskBookingView,
    FrontDeskClassView,
    FrontDeskSessionView,
    SessionCapacity,
)

# --------------------------------------------------------------------------- #
# GymClass
# --------------------------------------------------------------------------- #
from .gym_class import (
    GymClassBase,
    GymClassCreate,
    GymClassInClassScheduleResponse,
    GymClassInTeacherResponse,
    GymClassPublic,
    GymClassRead,
    GymClassUpdate,
    GymClassWithSchedules,
)

# --------------------------------------------------------------------------- #
# Membership
# --------------------------------------------------------------------------- #
from .membership import (
    Membership,
    MembershipBase,
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    MembershipWithClient,
    MembershipWithStats,
)

# --------------------------------------------------------------------------- #
# Person
# --------------------------------------------------------------------------- #
from .person import PersonBase, PersonCreate, PersonUpdate

# --------------------------------------------------------------------------- #
# Teacher
# --------------------------------------------------------------------------- #
from .teacher import (
    Teacher,
    TeacherBase,
    TeacherCreate,
    TeacherInClassScheduleResponse,
    TeacherInScheduleResponseMini,
    TeacherPublic,
    TeacherUpdate,
    TeacherWithMetrics,
    TeacherWithNextSession,
    TeacherWithSchedules,
)

# --------------------------------------------------------------------------- #
# Token
# --------------------------------------------------------------------------- #
from .token import Token, TokenPayload

# --------------------------------------------------------------------------- #
# User
# --------------------------------------------------------------------------- #
from .user import (
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserUpdate,
    UserWithProfile,
    UserWithStats,
)

# --------------------------------------------------------------------------- #
# Model rebuild (solo los que tienen forward refs)
# --------------------------------------------------------------------------- #

GymClassRead.model_rebuild()
GymClassWithSchedules.model_rebuild()

ClassSchedule.model_rebuild()
ClassSchedulePublic.model_rebuild()
ClassScheduleWithNextSession.model_rebuild()

ClassSession.model_rebuild()
ClassSessionWithSchedule.model_rebuild()
ClassSessionWithNext.model_rebuild()

Booking.model_rebuild()
BookingWithSession.model_rebuild()
BookingWithClient.model_rebuild()

Client.model_rebuild()
ClientWithBookings.model_rebuild()
ClientWithMembership.model_rebuild()
ClientWithStats.model_rebuild()

Membership.model_rebuild()
MembershipPublic.model_rebuild()
MembershipWithClient.model_rebuild()
MembershipWithStats.model_rebuild()

Teacher.model_rebuild()
TeacherPublic.model_rebuild()

User.model_rebuild()
UserWithProfile.model_rebuild()
UserWithStats.model_rebuild()

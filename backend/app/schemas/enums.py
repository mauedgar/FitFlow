# app/schemas/enums.py
from enum import StrEnum

class UserRole(StrEnum):
    admin = "admin"
    teacher = "teacher"
    client = "client"

class DifficultyLevel(StrEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class BookingStatus(StrEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    attended = "attended"
    no_show = "no_show"

class ClassSessionStatus(StrEnum):
    scheduled = "scheduled"
    cancelled = "cancelled"
    completed = "completed"

class MembershipPlan(StrEnum):
    gym_only = "gym_only"
    classes = "classes"
    premium = "premium"
    personalized = "personalized"

class MembershipStatus(StrEnum):
    active = "active"
    expired = "expired"
    paused = "paused"
    cancelled = "cancelled"

class ActivityType(StrEnum):
    group_class = "group_class"
    open_gym = "open_gym"
    personal_training = "personal_training"

class AllowedPlan(StrEnum):
    classes = "classes"
    premium = "premium"
    personalized = "personalized"
from typing import get_origin

from sqlalchemy.orm import Mapped, configure_mappers

from app.core.enums import ClassSessionStatus
from app.db.base import Base
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Person,
    Teacher,
    User,
)


ACTIVE_TABLES = {
    "bookings",
    "class_schedules",
    "class_sessions",
    "clients",
    "gym_classes",
    "memberships",
    "persons",
    "teachers",
    "users",
}
ACTIVE_MODELS = (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Person,
    Teacher,
    User,
)


def test_active_metadata_and_mappers_load() -> None:
    configure_mappers()
    assert set(Base.metadata.tables) == ACTIVE_TABLES
    assert len(list(Base.registry.mappers)) == len(ACTIVE_MODELS)


def test_every_local_column_uses_mapped_annotation() -> None:
    for model in ACTIVE_MODELS:
        for column in model.__table__.columns:
            annotation = next(
                (
                    parent.__dict__["__annotations__"][column.key]
                    for parent in model.__mro__
                    if column.key in parent.__dict__.get("__annotations__", {})
                ),
                None,
            )
            is_mapped = get_origin(annotation) is Mapped or (
                isinstance(annotation, str) and annotation.startswith("Mapped[")
            )
            assert is_mapped, (
                f"{model.__name__}.{column.key} must use Mapped[T]"
            )


def test_relationships_reject_implicit_async_lazy_loading() -> None:
    for mapper in Base.registry.mappers:
        for relationship in mapper.relationships:
            assert relationship.lazy == "raise", (
                f"{mapper.class_.__name__}.{relationship.key} must use lazy='raise'"
            )


def test_existing_cascade_semantics_are_preserved() -> None:
    full_orphan_cascade = {
        "delete",
        "delete-orphan",
        "expunge",
        "merge",
        "refresh-expire",
        "save-update",
    }
    expected = {
        ("User", "person_profile"): full_orphan_cascade,
        ("Client", "bookings"): full_orphan_cascade,
        ("Client", "membership"): full_orphan_cascade,
        ("GymClass", "class_schedules"): full_orphan_cascade,
        ("ClassSchedule", "class_sessions"): full_orphan_cascade,
    }
    actual = {
        (mapper.class_.__name__, relationship.key): set(relationship.cascade)
        for mapper in Base.registry.mappers
        for relationship in mapper.relationships
        if "delete-orphan" in relationship.cascade
    }
    assert actual == expected


def test_existing_on_delete_semantics_are_preserved() -> None:
    expected = {
        ("bookings", "client_id"): "CASCADE",
        ("bookings", "class_session_id"): "CASCADE",
        ("class_schedules", "gym_class_id"): "CASCADE",
        ("class_schedules", "teacher_id"): "CASCADE",
        ("class_schedules", "created_by_id"): "SET NULL",
        ("class_schedules", "updated_by_id"): "SET NULL",
        ("class_sessions", "class_schedule_id"): "CASCADE",
        ("clients", "id"): None,
        ("memberships", "client_id"): None,
        ("persons", "user_id"): None,
        ("teachers", "id"): None,
    }
    actual: dict[tuple[str, str], str | None] = {}
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            actual[(table.name, foreign_key.parent.name)] = foreign_key.ondelete
    assert actual == expected


def test_session_status_contract_is_aligned() -> None:
    assert [status.value for status in ClassSessionStatus] == [
        "scheduled",
        "open",
        "closed",
        "cancelled",
        "completed",
    ]


def test_schedule_mapping_uses_rrule_as_the_only_recurrence_source() -> None:
    columns = set(ClassSchedule.__table__.columns.keys())
    assert "rrule" in columns
    assert "days_of_week" not in columns
    assert {"created_by_id", "updated_by_id"}.issubset(columns)

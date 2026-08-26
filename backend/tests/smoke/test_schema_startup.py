"""Startup checks for schema imports and generated API contracts."""

import pytest

from app.main import app
from app.schemas.class_schedule import ClassSchedulePublic
from app.schemas.class_schedule_refs import (
    ClassSchedulePublic as ClassSchedulePublicRef,
)
from app.schemas.gym_class import (
    GymClassPublic,
    GymClassWithRelations,
    GymClassWithSchedules,
)
from app.schemas.gym_class_refs import GymClassPublic as GymClassPublicRef


@pytest.mark.smoke
def test_schema_registries_preserve_public_exports() -> None:
    """Public schema modules reexport the registry contracts unchanged."""
    assert ClassSchedulePublic is ClassSchedulePublicRef
    assert GymClassPublic is GymClassPublicRef
    assert GymClassWithRelations.model_json_schema()
    assert GymClassWithSchedules.model_json_schema()


@pytest.mark.smoke
def test_app_generates_openapi_contract() -> None:
    """Application startup reaches deterministic OpenAPI generation."""
    schema = app.openapi()

    assert schema["openapi"]
    assert schema["paths"]

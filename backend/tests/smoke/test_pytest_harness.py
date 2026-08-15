import sys

import pytest
from sqlalchemy.orm import configure_mappers

from app.db.base import Base


@pytest.mark.smoke
def test_pytest_harness_uses_supported_python_runtime() -> None:
    """The test image uses the backend's supported Python baseline."""
    assert sys.version_info >= (3, 11)


@pytest.mark.smoke
def test_orm_metadata_and_mappers_load() -> None:
    """The backend's active ORM registry can load without touching a database."""
    configure_mappers()

    assert set(Base.metadata.tables) == {
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

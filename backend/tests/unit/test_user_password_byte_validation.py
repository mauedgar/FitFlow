"""Schema boundary for bcrypt password creation/update (synthetic only)."""

from __future__ import annotations

import pytest
from app.schemas.user import UserCreate, UserUpdate
from pydantic import ValidationError


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37, "test\x00password"])
def test_user_create_rejects_password_not_representable_by_bcrypt(password: str) -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="candidate43@example.com", password=password)


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37, "test\x00password"])
def test_user_update_rejects_password_not_representable_by_bcrypt(password: str) -> None:
    with pytest.raises(ValidationError):
        UserUpdate(password=password)


def test_72_byte_boundary_and_optional_update_are_preserved() -> None:
    assert UserCreate(email="candidate43@example.com", password="ñ" * 36).password == "ñ" * 36
    assert UserUpdate(password="a" * 72).password == "a" * 72
    assert UserUpdate(password=None).password is None
    assert UserUpdate().password is None

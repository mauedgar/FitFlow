"""Schema boundary for bcrypt password creation/update (synthetic only)."""

from __future__ import annotations

import pytest
from app.schemas.user import (
    PublicClientRegistration,
    PublicUserRegistration,
    UserCreate,
    UserUpdate,
)
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


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37, "test\x00password"])
def test_both_public_registration_schemas_reject_nonrepresentable_password(password: str) -> None:
    with pytest.raises(ValidationError):
        PublicUserRegistration(email="user@example.com", password=password)
    with pytest.raises(ValidationError):
        PublicClientRegistration(
            email="client@example.com",
            password=password,
            first_name="Ana",
            last_name="Pérez García",
        )


@pytest.mark.parametrize("password", ["a" * 72, "ñ" * 36, "a" * 70 + "ñ"])
def test_public_registration_password_exact_72_utf8_bytes(password: str) -> None:
    assert len(password.encode("utf-8")) == 72
    assert PublicUserRegistration(email="user@example.com", password=password).password == password
    client = PublicClientRegistration(
        email="client@example.com",
        password=password,
        first_name="Ana María",
        last_name="Pérez García",
    )
    assert client.password == password
    assert client.last_name == "Pérez García"

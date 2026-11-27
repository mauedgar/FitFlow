"""Synthetic bcrypt compatibility at HTTP login without retained writes."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import bcrypt
import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.routers import auth as auth_router
from fastapi import status

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class SyntheticUser:
    id: UUID
    hashed_password: str
    role: UserRole = UserRole.client
    active: bool = True
    deleted_at: object | None = None


@pytest.mark.parametrize(
    "stored_hash",
    [
        "not-a-hash",
        "🚫" * 60,
        "$2b$99$abcdefghijklmnopqrstuu" + "a" * 31,
        "$2b$12$too-short",
    ],
)
async def test_malformed_or_nonascii_hash_fails_closed_without_session_write(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    stored_hash: str,
) -> None:
    user = SyntheticUser(id=uuid4(), hashed_password=stored_hash)

    async def lookup(*, db: object, email: str) -> SyntheticUser:
        del db
        assert email == "issue43@example.com"
        return user

    async def unexpected_register(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Malformed hash must not register any durable session")

    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(auth_router.session_ledger, "register", unexpected_register)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "issue43@example.com", "password": "contraseña"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": "Correo o contraseña incorrectos"}
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_legacy_overlong_password_hash_authenticates_without_rehash(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_digest = bcrypt.hashpw(
        ("a" * 72).encode("utf-8"), b"$2b$04$abcdefghijklmnopqrstuu"
    ).decode("ascii")
    user = SyntheticUser(id=uuid4(), hashed_password=legacy_digest)
    recorded: list[tuple[UUID, str]] = []

    async def lookup(*, db: object, email: str) -> SyntheticUser:
        del db
        assert email == "issue43@example.com"
        return user

    async def register(_db: object, *, subject: UUID, refresh_token: str) -> None:
        recorded.append((subject, refresh_token))

    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(auth_router.session_ledger, "register", register)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "issue43@example.com", "password": "a" * 73},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["access_token"]
    assert recorded and recorded[0][0] == user.id
    assert user.hashed_password == legacy_digest  # No hash reset or rehash.

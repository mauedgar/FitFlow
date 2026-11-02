"""Real FastAPI login mapping for synthetic bcrypt hashes; no DB or Redis writes."""

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


@pytest.mark.parametrize(
    "stored_hash",
    [
        "not-a-hash",
        "🚫" * 60,
        "$2b$99$abcdefghijklmnopqrstuu" + "a" * 31,
        "$2b$12$too-short",
    ],
)
async def test_malformed_or_nonascii_stored_hash_login_returns_401_not_500(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    stored_hash: str,
) -> None:
    user = SyntheticUser(id=uuid4(), hashed_password=stored_hash)

    async def fake_lookup(*, db: object, email: str) -> SyntheticUser:
        del db
        assert email == "issue43@example.com"
        return user

    def unexpected_store(_user_id: str, _token: str) -> None:
        pytest.fail("Malformed hash must not create a refresh session")

    monkeypatch.setattr(auth_router, "user_get_by_email", fake_lookup)
    monkeypatch.setattr(auth_router, "store_refresh_token", unexpected_store)

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "issue43@example.com", "password": "contraseña"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": "Correo o contraseña incorrectos"}
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_legacy_overlong_password_login_still_works_without_rehash(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulates an existing Passlib-era bcrypt digest, never a real account.
    legacy_digest = bcrypt.hashpw(
        ("a" * 72).encode("utf-8"), b"$2b$04$abcdefghijklmnopqrstuu"
    ).decode("ascii")
    user = SyntheticUser(id=uuid4(), hashed_password=legacy_digest)
    stored: list[tuple[str, str]] = []

    async def fake_lookup(*, db: object, email: str) -> SyntheticUser:
        del db
        assert email == "issue43@example.com"
        return user

    monkeypatch.setattr(auth_router, "user_get_by_email", fake_lookup)
    monkeypatch.setattr(
        auth_router,
        "store_refresh_token",
        lambda user_id, token: stored.append((user_id, token)),
    )

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "issue43@example.com", "password": "a" * 73},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["access_token"]
    assert stored and stored[0][0] == str(user.id)
    assert user.hashed_password == legacy_digest  # No rehash or DB mutation.

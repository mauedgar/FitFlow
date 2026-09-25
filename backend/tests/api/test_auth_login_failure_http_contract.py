"""HTTP contract for login success and bounded login failure behavior."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx
import pytest
from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.routers import auth as auth_router
from fastapi import status

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@dataclass(frozen=True)
class LoginUserStub:
    id: uuid.UUID
    hashed_password: str = "synthetic-hash"
    role: UserRole = UserRole.client


async def _post_login(
    api_client: httpx.AsyncClient,
    *,
    username: str = "r005@example.com",
    password: str = "FitFlow-R005-Password",
) -> httpx.Response:
    return await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": username, "password": password},
    )


async def test_login_success_returns_token_pair_and_preserves_user_id_subject(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())
    stored: list[tuple[str, str]] = []

    async def get_user(*, db: object, email: str) -> LoginUserStub:
        del db
        assert email == "r005@example.com"
        return user

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda _plain, _hashed: True)
    monkeypatch.setattr(
        auth_router,
        "store_refresh_token",
        lambda user_id, token: stored.append((user_id, token)),
    )

    response = await _post_login(api_client)

    assert response.status_code == status.HTTP_200_OK, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]

    access_payload = security.decode_token(body["access_token"])
    refresh_payload = security.decode_token(body["refresh_token"])
    assert access_payload is not None
    assert refresh_payload is not None
    assert access_payload["sub"] == str(user.id)
    assert access_payload["role"] == UserRole.client.value
    assert refresh_payload["sub"] == str(user.id)
    assert stored == [(str(user.id), body["refresh_token"])]


async def test_login_invalid_password_returns_401_without_refresh_store(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())
    stored: list[str] = []

    async def get_user(*, db: object, email: str) -> LoginUserStub:
        del db, email
        return user

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda _plain, _hashed: False)
    monkeypatch.setattr(
        auth_router,
        "store_refresh_token",
        lambda _user_id, _token: stored.append("store"),
    )

    response = await _post_login(api_client, password="definitely-wrong")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Correo o contraseña incorrectos"}
    assert response.headers.get("www-authenticate") == "Bearer"
    assert stored == []


async def test_login_nonexistent_user_returns_same_401_without_password_check_or_store(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    async def get_user(*, db: object, email: str) -> None:
        del db, email

    def should_not_verify(_plain: str, _hashed: str) -> bool:
        events.append("verify")
        raise AssertionError("password verification must be short-circuited")

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", should_not_verify)
    monkeypatch.setattr(
        auth_router,
        "store_refresh_token",
        lambda _user_id, _token: events.append("store"),
    )

    response = await _post_login(api_client, username="missing-r005@example.com")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Correo o contraseña incorrectos"}
    assert response.headers.get("www-authenticate") == "Bearer"
    assert events == []


async def test_login_missing_password_preserves_framework_422_boundary(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "r005@example.com"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_login_user_lookup_external_service_error_maps_to_503(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable(*, db: object, email: str) -> None:
        del db, email
        raise auth_router.ExternalServiceError("Login dependency unavailable.")

    monkeypatch.setattr(auth_router, "user_get_by_email", unavailable)

    response = await _post_login(api_client)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Login dependency unavailable."}


async def test_login_user_lookup_generic_failure_maps_to_500(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def failing_lookup(*, db: object, email: str) -> None:
        del db, email
        raise RuntimeError("synthetic lookup failure")

    monkeypatch.setattr(auth_router, "user_get_by_email", failing_lookup)

    response = await _post_login(api_client)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}


async def test_login_refresh_store_external_service_error_maps_to_503(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())

    async def get_user(*, db: object, email: str) -> LoginUserStub:
        del db, email
        return user

    def unavailable_store(_user_id: str, _token: str) -> None:
        raise auth_router.ExternalServiceError("Redis no está disponible.")

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda _plain, _hashed: True)
    monkeypatch.setattr(auth_router, "store_refresh_token", unavailable_store)

    response = await _post_login(api_client)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está disponible."}


async def test_login_refresh_store_generic_failure_maps_to_500(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())

    async def get_user(*, db: object, email: str) -> LoginUserStub:
        del db, email
        return user

    def failing_store(_user_id: str, _token: str) -> None:
        raise RuntimeError("synthetic refresh-store failure")

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda _plain, _hashed: True)
    monkeypatch.setattr(auth_router, "store_refresh_token", failing_store)

    response = await _post_login(api_client)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}

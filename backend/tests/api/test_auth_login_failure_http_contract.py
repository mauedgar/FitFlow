"""Real HTTP API login: new modern SID issuance, failures and no false ACK."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx
import pytest
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class LoginUserStub:
    id: uuid.UUID
    hashed_password: str = "synthetic-hash"
    role: UserRole = UserRole.client
    active: bool = True
    deleted_at: object | None = None


async def _post_login(
    api_client: httpx.AsyncClient,
    *, username: str = "r005@example.com", password: str = "FitFlow-R005-Password",
) -> httpx.Response:
    return await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": username, "password": password},
    )


async def test_login_success_returns_persisted_modern_sid_token_pair(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())
    recorded: list[tuple[uuid.UUID, str]] = []

    async def lookup(*, db: object, email: str) -> LoginUserStub:
        del db
        assert email == "r005@example.com"
        return user

    async def register(_db: object, *, subject: uuid.UUID, refresh_token: str) -> None:
        recorded.append((subject, refresh_token))

    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda *_: True)
    monkeypatch.setattr(auth_router.session_ledger, "register", register)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_200_OK, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    access = security.decode_token(body["access_token"])
    refresh = security.decode_token(body["refresh_token"])
    assert access is not None and refresh is not None
    assert access["sub"] == refresh["sub"] == str(user.id)
    assert access["role"] == UserRole.client.value
    assert access["token_use"] == "access" and refresh["token_use"] == "refresh"
    assert "role" not in refresh
    assert access["sid"] == refresh["sid"] == str(uuid.UUID(access["sid"]))
    assert recorded == [(user.id, body["refresh_token"])]


@pytest.mark.parametrize("condition", ["wrong_password", "missing", "inactive", "deleted"])
async def test_failed_login_never_registers_any_session(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
    condition: str,
) -> None:
    user = LoginUserStub(
        id=uuid.uuid4(), active=condition != "inactive",
        deleted_at="deleted" if condition == "deleted" else None,
    )
    writes: list[str] = []

    async def lookup(*, db: object, email: str) -> LoginUserStub | None:
        del db, email
        return None if condition == "missing" else user

    async def register(*_args: object, **_kwargs: object) -> None:
        writes.append("durable-register")

    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(
        auth_router.security, "verify_password",
        lambda *_: condition != "wrong_password",
    )
    monkeypatch.setattr(auth_router.session_ledger, "register", register)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": "Correo o contraseña incorrectos"}
    assert response.headers.get("www-authenticate") == "Bearer"
    assert writes == []


async def test_login_missing_password_preserves_http_422(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token", data={"username": "r005@example.com"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_login_lookup_external_error_returns_503(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable(*, db: object, email: str) -> None:
        del db, email
        raise auth_router.ExternalServiceError("Login dependency unavailable.")

    monkeypatch.setattr(auth_router, "user_get_by_email", unavailable)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Login dependency unavailable."}


async def test_login_lookup_sqlalchemy_error_maps_to_503(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database outage must not become a generic 500 on the /auth/token alias."""
    async def unavailable(*, db: object, email: str) -> None:
        del db, email
        raise SQLAlchemyError("synthetic DB details must never reach client")

    monkeypatch.setattr(auth_router, "user_get_by_email", unavailable)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Persistencia de sesiones no disponible."}
    assert "synthetic DB details" not in response.text


async def test_login_lookup_generic_failure_maps_to_500(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def broken(*, db: object, email: str) -> None:
        del db, email
        raise RuntimeError("synthetic lookup failure")

    monkeypatch.setattr(auth_router, "user_get_by_email", broken)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}


@pytest.mark.parametrize("failure", ["db_error", "unknown_commit"])
async def test_login_fails_closed_when_pg_registration_not_confirmed(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())

    async def lookup(*, db: object, email: str) -> LoginUserStub:
        del db, email
        return user

    async def broken_register(*_args: object, **_kwargs: object) -> None:
        if failure == "db_error":
            raise auth_router.ExternalServiceError("synthetic database down")
        raise RuntimeError("synthetic unknown COMMIT outcome")

    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda *_: True)
    monkeypatch.setattr(auth_router.session_ledger, "register", broken_register)
    response = await _post_login(api_client)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.text
    assert response.json() == {"detail": "Persistencia de sesiones no disponible."}
    assert "access_token" not in response.text
    assert "refresh_token" not in response.text

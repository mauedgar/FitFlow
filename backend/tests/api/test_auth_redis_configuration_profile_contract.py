"""HTTP contract for Redis configuration/profile boundaries in auth."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
import pytest
from fastapi import status
from redis.exceptions import RedisError

from app.core import redis_client, security
from app.core.config import Settings, settings
from app.core.deps import get_current_user
from app.core.enums import UserRole
from app.main import app
from app.routers import auth as auth_router

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]

SUPPORTED_PROFILES = ("development", "test")


@dataclass(frozen=True)
class LoginUserStub:
    id: uuid.UUID
    hashed_password: str = "synthetic-hash"
    role: UserRole = UserRole.client


@dataclass(frozen=True)
class CurrentUserStub:
    id: uuid.UUID


@pytest.fixture
async def authenticated_owner() -> AsyncIterator[uuid.UUID]:
    owner_id = uuid.uuid4()

    async def override_current_user() -> CurrentUserStub:
        return CurrentUserStub(id=owner_id)

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        yield owner_id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize("profile", SUPPORTED_PROFILES)
async def test_supported_profile_settings_allow_redis_to_be_unconfigured(
    profile: str,
) -> None:
    configured = Settings(
        _env_file=None,
        ENV=profile,
        DEBUG=profile == "development",
        TESTING=profile == "test",
        DATABASE_URL="postgresql://fitflow:fitflow@localhost/fitflow_contract",
        SECRET_KEY="redis-profile-contract-secret",
        REDIS_URL=None,
    )

    assert configured.ENV == profile
    assert configured.REDIS_URL is None


async def test_non_redis_route_remains_available_when_redis_is_unconfigured(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", None)

    response = await api_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to FitFlow API"}


async def test_login_returns_503_when_redis_is_unconfigured(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = LoginUserStub(id=uuid.uuid4())

    async def get_user(*, db: object, email: str) -> LoginUserStub:
        del db, email
        return user

    monkeypatch.setattr(settings, "REDIS_URL", None)
    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda _plain, _hashed: True)

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "redis-contract@example.com", "password": "synthetic-password"},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está configurado."}


async def test_refresh_returns_503_when_redis_is_unconfigured(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", None)

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "opaque-refresh-token"},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está configurado."}


async def test_logout_returns_503_when_redis_is_unconfigured(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", None)
    refresh_token = security.create_refresh_token(data={"sub": str(authenticated_owner)})

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está configurado."}


async def test_refresh_returns_503_when_configured_redis_is_unavailable(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnavailableRedisClient:
        def ping(self) -> None:
            raise RedisError("synthetic Redis outage")

    monkeypatch.setattr(settings, "REDIS_URL", "redis://configured-but-unavailable:6379/0")
    monkeypatch.setattr(
        redis_client.Redis,
        "from_url",
        lambda *_args, **_kwargs: UnavailableRedisClient(),
    )

    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "opaque-refresh-token"},
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está disponible."}

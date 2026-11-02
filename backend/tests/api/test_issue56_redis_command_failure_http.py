"""IR005 F09 failure-after-ping contract (no external Redis or DB state)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import httpx
import pytest
from app.core import redis_client, security
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.enums import UserRole
from app.main import app
from app.routers import auth as auth_router
from redis.exceptions import RedisError

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class SyntheticUser:
    id: UUID
    hashed_password: str = "synthetic"
    role: UserRole = UserRole.client
    active: bool = True


class BrokenAfterPing:
    def ping(self) -> bool:
        return True

    def set(self, *args: object, **kwargs: object) -> None:
        raise RedisError("synthetic command outage")

    def exists(self, *args: object, **kwargs: object) -> None:
        raise RedisError("synthetic command outage")

    def delete(self, *args: object, **kwargs: object) -> None:
        raise RedisError("synthetic command outage")

    def eval(self, *args: object, **kwargs: object) -> None:
        raise RedisError("synthetic command outage")

    def close(self) -> None:
        pass


@pytest.fixture
def broken_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setattr(
        redis_client.Redis, "from_url",
        lambda *_args, **_kwargs: BrokenAfterPing(),
    )


async def test_refresh_command_error_after_ping_maps_503(
    api_client: httpx.AsyncClient, broken_redis: None,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "invalid-input"},
    )
    assert response.status_code == 503, response.text
    assert response.json() == {"detail": "Redis no está disponible."}


async def test_login_store_command_error_after_ping_maps_503(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    broken_redis: None,
) -> None:
    user = SyntheticUser(id=uuid4())

    async def get_user(*, db: object, email: str) -> SyntheticUser:
        del db, email
        return user

    monkeypatch.setattr(auth_router, "user_get_by_email", get_user)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda *_: True)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "synthetic@invalid.test", "password": "test"},
    )
    assert response.status_code == 503, response.text
    assert response.json() == {"detail": "Redis no está disponible."}


async def test_logout_command_error_after_ping_maps_503(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    broken_redis: None,
) -> None:
    identity = uuid4()
    token = security.create_refresh_token({"sub": str(identity)})

    async def stub_user() -> SyntheticUser:
        return SyntheticUser(id=identity)

    app.dependency_overrides[get_current_user] = stub_user
    try:
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": token},
        )
        assert response.status_code == 503, response.text
        assert response.json() == {"detail": "Redis no está disponible."}
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_non_test_login_limiter_redis_after_ping_maps_503_before_db(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    broken_redis: None,
) -> None:
    calls: list[str] = []

    async def forbidden_lookup(*, db: object, email: str) -> None:
        del db, email
        calls.append("lookup")
        raise AssertionError("Throttled failure must not reach DB lookup")

    monkeypatch.setattr(settings, "TESTING", False)
    monkeypatch.setattr(auth_router, "user_get_by_email", forbidden_lookup)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "limiter@example.invalid", "password": "synthetic"},
    )
    assert response.status_code == 503, response.text
    assert response.json() == {"detail": "Redis no está disponible."}
    assert calls == []


async def test_non_test_login_limiter_missing_redis_maps_503(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TESTING", False)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "limiter@example.invalid", "password": "synthetic"},
    )
    assert response.status_code == 503, response.text
    assert response.json() == {"detail": "Redis no está configurado."}

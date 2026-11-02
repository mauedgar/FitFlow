"""IR004 integration regression: role renewal, unique refresh, Redis TTL and inactive users.

Run only against synthetic fitflow_test PG15 and local disposable Redis7.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, tzinfo
from uuid import UUID, uuid4

import httpx
import pytest
from app.core import security
from app.core.blacklist import BLACKLIST_PREFIX
from app.core.config import Settings, settings
from app.core.redis_client import get_redis_client
from app.core.token_store import REFRESH_PREFIX
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.core.enums import UserRole
from sqlalchemy import delete, update
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]
PASSWORD = "IR004-Only-Synthetic-Password-42!"


@pytest.fixture(autouse=True)
def require_isolated_services() -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"
    assert settings.REDIS_URL == "redis://127.0.0.1:6379/0"


@pytest.fixture(autouse=True)
async def dispose_engine() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def principal() -> AsyncIterator[tuple[UUID, str]]:
    uid = uuid4()
    email = f"ir004-auth-{uid.hex}@example.com"
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=uid,
            email=email,
            hashed_password=security.get_password_hash(PASSWORD),
            role=UserRole.client,
            active=True,
        ))
        await db.commit()
    try:
        yield uid, email
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == uid))
            await db.commit()


@pytest.fixture
def cleanup_redis() -> Iterator[list[str]]:
    tokens: list[str] = []
    yield tokens
    client = get_redis_client()
    try:
        for token in tokens:
            client.delete(
                f"{REFRESH_PREFIX}{token}", f"{BLACKLIST_PREFIX}{token}",
            )
    finally:
        client.close()


async def login(
    api_client: httpx.AsyncClient, email: str,
) -> httpx.Response:
    return await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": PASSWORD},
    )


async def test_refresh_role_matches_database_and_frontend_contract(
    api_client: httpx.AsyncClient, principal: tuple[UUID, str],
    cleanup_redis: list[str],
) -> None:
    uid, email = principal
    issued = await login(api_client, email)
    assert issued.status_code == 200, issued.text
    refresh = issued.json()["refresh_token"]
    cleanup_redis.append(refresh)
    renewed = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert renewed.status_code == 200, renewed.text
    assert set(renewed.json()) == {"access_token", "token_type"}
    decoded = security.decode_token(renewed.json()["access_token"])
    assert decoded is not None
    assert decoded["sub"] == str(uid)
    assert decoded["role"] == UserRole.client.value
    assert decoded["token_use"] == "access"
    # The existing frontend AuthProvider takes userRole from decoded.role.
    me = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {renewed.json()['access_token']}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["role"] == decoded["role"]


async def test_same_second_login_logout_login_does_not_revoke_new_refresh(
    api_client: httpx.AsyncClient, principal: tuple[UUID, str],
    cleanup_redis: list[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, email = principal
    frozen = datetime.now(UTC)

    class FixedClock:
        @staticmethod
        def now(*, tz: tzinfo | None = None) -> datetime:
            return frozen

    monkeypatch.setattr(security, "datetime", FixedClock)
    first = await login(api_client, email)
    assert first.status_code == 200, first.text
    first_tokens = first.json()
    cleanup_redis.append(first_tokens["refresh_token"])
    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": first_tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {first_tokens['access_token']}"},
    )
    assert logout.status_code == 204, logout.text

    second = await login(api_client, email)
    assert second.status_code == 200, second.text
    second_tokens = second.json()
    cleanup_redis.append(second_tokens["refresh_token"])
    old_claim = security.decode_token(first_tokens["refresh_token"])
    new_claim = security.decode_token(second_tokens["refresh_token"])
    assert old_claim is not None and new_claim is not None
    assert old_claim["exp"] == new_claim["exp"]
    assert old_claim["jti"] != new_claim["jti"]
    assert first_tokens["refresh_token"] != second_tokens["refresh_token"]

    current = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": second_tokens["refresh_token"]},
    )
    assert current.status_code == 200, current.text
    previous = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": first_tokens["refresh_token"]},
    )
    assert previous.status_code == 401, previous.text


async def test_redis_refresh_and_blacklist_entries_have_bounded_ttl(
    api_client: httpx.AsyncClient, principal: tuple[UUID, str],
    cleanup_redis: list[str],
) -> None:
    _, email = principal
    issued = await login(api_client, email)
    assert issued.status_code == 200, issued.text
    token = issued.json()["refresh_token"]
    cleanup_redis.append(token)
    client = get_redis_client()
    try:
        ttl = client.ttl(f"{REFRESH_PREFIX}{token}")
        assert 0 < ttl <= settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": token},
            headers={"Authorization": f"Bearer {issued.json()['access_token']}"},
        )
        assert logout.status_code == 204, logout.text
        assert client.exists(f"{REFRESH_PREFIX}{token}") == 0
        blacklisted_ttl = client.ttl(f"{BLACKLIST_PREFIX}{token}")
        assert 0 < blacklisted_ttl <= settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
    finally:
        client.close()


async def test_inactive_account_login_and_refresh_denied(
    api_client: httpx.AsyncClient, principal: tuple[UUID, str],
    cleanup_redis: list[str],
) -> None:
    uid, email = principal
    issued = await login(api_client, email)
    assert issued.status_code == 200, issued.text
    cleanup_redis.append(issued.json()["refresh_token"])
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.id == uid).values(active=False))
        await db.commit()

    denied_login = await login(api_client, email)
    assert denied_login.status_code == 401, denied_login.text
    assert denied_login.json() == {"detail": "Correo o contraseña incorrectos"}
    denied_refresh = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": issued.json()["refresh_token"]},
    )
    assert denied_refresh.status_code == 401, denied_refresh.text
    assert "ir004-auth-" not in denied_refresh.text


async def test_deleted_account_cannot_renew_refresh(
    api_client: httpx.AsyncClient, principal: tuple[UUID, str],
    cleanup_redis: list[str],
) -> None:
    uid, email = principal
    issued = await login(api_client, email)
    assert issued.status_code == 200, issued.text
    cleanup_redis.append(issued.json()["refresh_token"])
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User).where(User.id == uid).values(deleted_at=datetime.now(UTC))
        )
        await db.commit()
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": issued.json()["refresh_token"]},
    )
    assert response.status_code == 401, response.text


async def test_rotation_is_explicitly_disabled_and_cannot_be_silently_enabled() -> None:
    assert settings.REFRESH_TOKEN_ROTATION is False
    with pytest.raises(ValueError, match="REFRESH_TOKEN_ROTATION=true is unsupported"):
        Settings(
            _env_file=None,  # pyright: ignore[reportCallIssue]
            ENV="test",
            DEBUG=False,
            TESTING=True,
            DATABASE_URL="postgresql://synthetic:synthetic@localhost/fitflow_test",
            SECRET_KEY="synthetic-only-key",
            REFRESH_TOKEN_ROTATION=True,
        )

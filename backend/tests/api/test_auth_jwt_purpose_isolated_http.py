"""Issue 108 — JWT purpose on synthetic disposable PostgreSQL only."""
from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import status
from jose import jwt
from sqlalchemy import update

from app.core import security
from auth_session_test_helpers import (
    cleanup_synthetic_fixture, committed_access, finish_synthetic_cleanup,
    require_local_test_database, require_local_test_redis, require_postgres15_test_service,
)
from app.core.blacklist import BLACKLIST_PREFIX, blacklist_token
from app.core.redis_client import get_redis_client
from app.core.config import settings
from app.core.token_store import REFRESH_PREFIX, store_refresh_token
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_db() -> None:
    require_local_test_database()


@pytest.fixture(autouse=True)
async def release_engine_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@asynccontextmanager
async def _synthetic_subject() -> AsyncIterator[uuid.UUID]:
    """No PostgreSQL writes until the exact test-service version is verified."""
    await require_postgres15_test_service()
    identifier = uuid.uuid4()
    try:
        async with AsyncSessionLocal() as db:
            db.add(User(
                id=identifier, email=f"jwt-purpose-{identifier.hex}@example.com",
                hashed_password=security.get_password_hash("synthetic-only"),
                role=UserRole.client, active=True,
            ))
            await db.commit()
        yield identifier
    finally:
        await finish_synthetic_cleanup(cleanup_synthetic_fixture(
            user_ids=(identifier,),
        ))


@pytest.fixture
async def subject() -> AsyncIterator[uuid.UUID]:
    async with _synthetic_subject() as identifier:
        yield identifier


@pytest.fixture
def real_redis7_preflight() -> None:
    """Skip and verify Redis before constructing any Redis test's PG user."""
    require_local_test_database()
    if os.getenv("GITHUB_ACTIONS") != "true":
        pytest.skip("Real Redis effects only on isolated GitHub Actions")
    require_local_test_redis()
    redis = get_redis_client()
    redis_major = int(redis.info(section="server")["redis_version"].split(".")[0])
    if redis_major != 7:
        raise RuntimeError("BLOCKED_PRECONDITION: Redis 7 test service required")


@pytest.fixture
async def redis_subject(real_redis7_preflight: None) -> AsyncIterator[uuid.UUID]:
    async with _synthetic_subject() as identifier:
        yield identifier


def cleanup_redis_test_token(token: str) -> None:
    """One exact-key cleanup after a possible SET, including uncertain ACK."""
    require_local_test_redis()
    redis = get_redis_client()
    keys = (
        opaque_jwt_key(REFRESH_PREFIX, token),
        legacy_jwt_key(REFRESH_PREFIX, token),
        f"{BLACKLIST_PREFIX}{token}",
    )
    # No sequential cleanup hole and no retry of a failed command.
    redis.delete(*keys)
    if redis.exists(*keys) != 0:
        raise RuntimeError("BLOCKED_POSTCONDITION: synthetic Redis token remains")


def legacy(subject: str, role: str | None) -> str:
    claims: dict[str, object] = {
        "sub": subject, "exp": datetime.now(tz=UTC) + timedelta(minutes=5),
    }
    if role is not None:
        claims["role"] = role
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def test_refresh_rejected_as_bearer_on_real_http(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    for token in (
        security.create_refresh_token({"sub": str(subject)}),
        legacy(str(subject), None),
    ):
        for route in ("/auth/me", "/users/public"):
            result = await api_client.get(
                f"{settings.API_V1_STR}{route}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text



async def test_registered_modern_access_and_legacy_denial_on_both_guards(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    live = await committed_access(subject, "client")
    valid = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {live}"},
    )
    assert valid.status_code == status.HTTP_200_OK, valid.text
    assert valid.json()["id"] == str(subject)
    for invalid in (
        security.create_access_token({"sub": str(subject), "role": "client"}),
        legacy(str(subject), "client"),
        security.create_access_token({
            "sub": str(subject), "role": "client", "sid": str(uuid.uuid4()),
        }),
        security.create_access_token({
            "sub": str(subject), "role": "client", "sid": "not-a-uuid",
        }),
    ):
        for route in ("/auth/me", "/users/public"):
            denied = await api_client.get(
                f"{settings.API_V1_STR}{route}",
                headers={"Authorization": f"Bearer {invalid}"},
            )
            assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text

async def test_access_cannot_refresh_even_if_registered(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _x: False)
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _x: True)
    for token in (
        security.create_access_token({"sub": str(subject), "role": "client"}),
        legacy(str(subject), "client"),
    ):
        result = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": token},
        )
        assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text



async def test_access_cannot_be_used_as_logout_refresh(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    token = await committed_access(subject, "client")
    result = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"refresh_token": token},
    )
    assert result.status_code == status.HTTP_400_BAD_REQUEST, result.text

async def test_registered_refresh_uses_current_database_role(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    """Modern refresh rehydrates the persisted role, not a refresh claim."""
    logged = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": f"jwt-purpose-{subject.hex}@example.com",
              "password": "synthetic-only"},
    )
    assert logged.status_code == status.HTTP_200_OK, logged.text
    refresh = logged.json()["refresh_token"]
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.id == subject).values(role=UserRole.teacher))
        await db.commit()
    result = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    payload = security.decode_token(result.json()["access_token"])
    assert payload is not None and payload["role"] == UserRole.teacher.value


async def test_untyped_legacy_refresh_cannot_mint_access(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    result = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": legacy(str(subject), None)},
    )
    assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text
    assert "access_token" not in result.text

async def test_refresh_rejects_inactive_missing_and_invalid_uuid(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _x: False)
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _x: True)
    for missing in (str(uuid.uuid4()), "invalid-uuid"):
        result = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": security.create_refresh_token({"sub": missing})},
        )
        assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.id == subject).values(active=False))
        await db.commit()
    result = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": security.create_refresh_token({"sub": str(subject)})},
    )
    assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text


async def test_signed_purpose_override_expiry_and_role_rules() -> None:
    subject = str(uuid.uuid4())
    access = security.decode_token(security.create_access_token({
        "sub": subject, "role": "client", "token_use": "refresh",
    }))
    refresh = security.decode_token(security.create_refresh_token({
        "sub": subject, "role": "admin", "token_use": "access",
    }))
    assert access is not None and refresh is not None
    assert access["token_use"] == "access"
    assert refresh["token_use"] == "refresh" and "role" not in refresh
    assert not security.is_access_token_payload(access)  # No SID, not a bearer.
    assert not security.is_refresh_token_payload(access)
    assert security.is_refresh_token_payload(refresh)
    assert not security.is_access_token_payload(refresh)
    assert not security.is_access_token_payload({"sub": subject, "role": "client"})
    assert not security.is_refresh_token_payload({"sub": subject})
    assert not security.is_access_token_payload(dict(access, token_use="unknown"))
    assert not security.is_access_token_payload(dict(access, exp=0))


async def test_actual_disposable_redis_registration_and_refresh(
    api_client: httpx.AsyncClient, redis_subject: uuid.UUID,
) -> None:
    """Real Redis7 registration: unregistered PG family remains denied."""
    subject = redis_subject
    if os.getenv("GITHUB_ACTIONS") != "true":
        pytest.skip("No real Redis effects outside isolated GitHub Actions CI")
    require_local_test_redis()
    token = security.create_refresh_token({"sub": str(subject)})
    try:
        store_refresh_token(str(subject), token)
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
        assert "access_token" not in response.text
        bearer = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bearer.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        cleanup_redis_test_token(token)


async def test_refresh_rejects_soft_deleted_active_account(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _token: False)
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _token: True)
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User).where(User.id == subject).values(
                deleted_at=datetime.now(tz=UTC), active=True,
            )
        )
        await db.commit()
    token = security.create_refresh_token({"sub": str(subject)})
    result = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": token},
    )
    assert result.status_code == status.HTTP_401_UNAUTHORIZED, result.text



async def test_signed_role_never_overrides_current_database_role(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    forged_role = await committed_access(subject, UserRole.admin.value)
    response = await api_client.get(
        f"{settings.API_V1_STR}/users/public",
        headers={"Authorization": f"Bearer {forged_role}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text

async def test_actual_disposable_redis_registration_blacklist_and_logout(
    api_client: httpx.AsyncClient, redis_subject: uuid.UUID,
) -> None:
    """Real Redis7 registration alone cannot authorize refresh or logout."""
    subject = redis_subject
    if os.getenv("GITHUB_ACTIONS") != "true":
        pytest.skip("Never touch real Redis outside disposable GitHub Actions CI")
    require_local_test_redis()

    refresh = security.create_refresh_token({"sub": str(subject)})
    access = security.create_access_token({
        "sub": str(subject), "role": "client",
    })
    redis = get_redis_client()
    assert redis.exists(f"{BLACKLIST_PREFIX}{refresh}") == 0
    # Signed token alone does not imply Redis registration.
    denied = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text

    try:
        store_refresh_token(str(subject), refresh)
        good = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert good.status_code == status.HTTP_401_UNAUTHORIZED, good.text

        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
            json={"refresh_token": refresh},
        )
        assert logout.status_code == status.HTTP_401_UNAUTHORIZED, logout.text
        assert redis.exists(f"{BLACKLIST_PREFIX}{refresh}") == 0

        denied_again = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert denied_again.status_code == status.HTTP_401_UNAUTHORIZED, denied_again.text
    finally:
        cleanup_redis_test_token(refresh)
    assert redis.exists(f"{BLACKLIST_PREFIX}{refresh}") == 0


async def test_actual_disposable_redis_blacklist_preempts_registered_refresh(
    api_client: httpx.AsyncClient, redis_subject: uuid.UUID,
) -> None:
    """Blacklisted but registered refresh fails on real ephemeral Redis."""
    subject = redis_subject
    if os.getenv("GITHUB_ACTIONS") != "true":
        pytest.skip("Never touch real Redis outside disposable GitHub Actions CI")
    require_local_test_redis()

    token = security.create_refresh_token({"sub": str(subject)})
    try:
        store_refresh_token(str(subject), token)
        blacklist_token(token)
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    finally:
        cleanup_redis_test_token(token)

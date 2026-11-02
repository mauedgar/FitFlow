"""PG15 + Redis7 HTTP proof: signed JWT type, legacy refresh, logout.

Fail-closed disposable fixture: no external database/Redis access.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from app.core import security
from app.core.blacklist import BLACKLIST_PREFIX, blacklist_key
from app.core.config import settings
from app.core.enums import UserRole
from app.core.redis_client import get_redis_client
from app.core.token_store import REFRESH_PREFIX, refresh_token_key, store_refresh_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from jose import jwt
from sqlalchemy import delete
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_services() -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"
    assert settings.REDIS_URL == "redis://127.0.0.1:6379/0"


@pytest.fixture(autouse=True)
async def dispose_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def owner_id() -> AsyncIterator[UUID]:
    identity = uuid4()
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=identity,
            email=f"jwt-purpose-{identity.hex}@example.com",
            hashed_password="synthetic-not-for-login",
            role=UserRole.client,
            active=True,
        ))
        await db.commit()
    try:
        yield identity
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == identity))
            await db.commit()


@pytest.fixture
def redis_cleanup() -> Iterator[list[str]]:
    # Scope all cleanup to exact synthetic credentials. Never FLUSHDB.
    tokens: list[str] = []
    yield tokens
    client = get_redis_client()
    for token in tokens:
        client.delete(
            f"{REFRESH_PREFIX}{token}", f"{BLACKLIST_PREFIX}{token}",
            refresh_token_key(token), blacklist_key(token),
        )
    client.close()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_refresh_never_authenticates_bearer_before_or_after_real_logout(
    api_client: httpx.AsyncClient, owner_id: UUID, redis_cleanup: list[str],
) -> None:
    access = security.create_access_token({"sub": str(owner_id)})
    refresh = security.create_refresh_token({"sub": str(owner_id)})
    access_payload = security.decode_token(access)
    refresh_payload = security.decode_token(refresh)
    assert access_payload is not None and access_payload["token_use"] == "access"
    assert refresh_payload is not None and refresh_payload["token_use"] == "refresh"
    redis_cleanup.append(refresh)
    store_refresh_token(str(owner_id), refresh)

    for path in ("/auth/me", "/users/public", f"/users/{owner_id}/public"):
        forbidden = await api_client.get(
            f"{settings.API_V1_STR}{path}", headers=bearer(refresh),
        )
        assert forbidden.status_code == 401, forbidden.text
        assert forbidden.headers.get("www-authenticate") == "Bearer"

    renewal = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
    )
    assert renewal.status_code == 200, renewal.text
    renewed_access = renewal.json()["access_token"]
    renewed_payload = security.decode_token(renewed_access)
    assert renewed_payload is not None
    assert renewed_payload["token_use"] == "access"
    identity = await api_client.get(
        f"{settings.API_V1_STR}/auth/me", headers=bearer(renewed_access),
    )
    assert identity.status_code == 200, identity.text
    assert identity.json()["id"] == str(owner_id)

    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers=bearer(access), json={"refresh_token": refresh},
    )
    assert logout.status_code == 204, logout.text
    rejected = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
    )
    assert rejected.status_code == 401, rejected.text
    assert rejected.json() == {"detail": "Refresh token invalidado."}
    no_bearer = await api_client.get(
        f"{settings.API_V1_STR}/users/{owner_id}/public", headers=bearer(refresh),
    )
    assert no_bearer.status_code == 401, no_bearer.text


async def test_registered_legacy_refresh_can_renew_and_logout_not_be_bearer(
    api_client: httpx.AsyncClient, owner_id: UUID, redis_cleanup: list[str],
) -> None:
    # Signed pre-migration token without token_use and role.
    legacy = jwt.encode(
        {"sub": str(owner_id),
         "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp())},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    legacy_payload = security.decode_token(legacy)
    assert legacy_payload is not None and "token_use" not in legacy_payload
    redis_cleanup.append(legacy)
    store_refresh_token(str(owner_id), legacy)

    forbidden = await api_client.get(
        f"{settings.API_V1_STR}/auth/me", headers=bearer(legacy),
    )
    assert forbidden.status_code == 401, forbidden.text
    renewal = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": legacy},
    )
    assert renewal.status_code == 200, renewal.text
    access = renewal.json()["access_token"]
    payload = security.decode_token(access)
    assert payload is not None and payload["token_use"] == "access"

    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers=bearer(access), json={"refresh_token": legacy},
    )
    assert logout.status_code == 204, logout.text
    revoked = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": legacy},
    )
    assert revoked.status_code == 401, revoked.text


async def test_unregistered_legacy_refresh_is_not_accepted(
    api_client: httpx.AsyncClient, owner_id: UUID,
) -> None:
    unregistered = jwt.encode(
        {"sub": str(owner_id),
         "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp())},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": unregistered},
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": "Refresh token no registrado."}


async def test_legacy_untyped_access_cannot_impersonate_refresh_or_bearer(
    api_client: httpx.AsyncClient, owner_id: UUID,
) -> None:
    legacy_access = jwt.encode(
        {"sub": str(owner_id), "role": "client",
         "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    me = await api_client.get(
        f"{settings.API_V1_STR}/auth/me", headers=bearer(legacy_access),
    )
    assert me.status_code == 401, me.text
    denied = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": legacy_access},
    )
    assert denied.status_code == 401, denied.text
    assert denied.json() == {"detail": "Refresh token inválido o expirado."}


async def test_typed_access_cannot_refresh_or_logout_even_if_redis_registered(
    api_client: httpx.AsyncClient, owner_id: UUID, redis_cleanup: list[str],
) -> None:
    access = security.create_access_token({"sub": str(owner_id)})
    redis_cleanup.append(access)
    store_refresh_token(str(owner_id), access)

    denied = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": access},
    )
    assert denied.status_code == 401, denied.text
    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers=bearer(access), json={"refresh_token": access},
    )
    assert logout.status_code == 400, logout.text
    assert logout.json() == {"detail": "Refresh token inválido."}


async def test_issuer_forces_signed_purpose_instead_of_caller_value() -> None:
    access = security.create_access_token({
        "sub": str(uuid4()), "token_use": "refresh",
    })
    refresh = security.create_refresh_token({
        "sub": str(uuid4()), "token_use": "access", "role": "admin",
    })
    payload_access = security.decode_token(access)
    payload_refresh = security.decode_token(refresh)
    assert payload_access is not None and payload_access["token_use"] == "access"
    assert payload_refresh is not None and payload_refresh["token_use"] == "refresh"
    assert "role" not in payload_refresh

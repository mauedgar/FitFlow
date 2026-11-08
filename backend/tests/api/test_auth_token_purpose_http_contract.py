"""JWT-purpose HTTP regression on disposable PostgreSQL15 and Redis7 only."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import status
from jose import jwt
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.core.redis_client import get_redis_client
from app.core.token_store import delete_refresh_token, store_refresh_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def user_id() -> AsyncIterator[uuid.UUID]:
    subject = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=subject,
            email=f"purpose-{subject.hex}@example.com",
            hashed_password=security.get_password_hash("synthetic-only"),
            role=UserRole.client,
            active=True,
        ))
        await db.commit()
    try:
        yield subject
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == subject))
            await db.commit()


def legacy(subject: uuid.UUID, role: str | None) -> str:
    payload: dict[str, object] = {
        "sub": str(subject),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=5),
    }
    if role is not None:
        payload["role"] = role
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def test_refresh_never_authenticates_as_bearer(
    api_client: httpx.AsyncClient, user_id: uuid.UUID,
) -> None:
    for token in (
        security.create_refresh_token({"sub": str(user_id)}),
        legacy(user_id, role=None),
    ):
        for endpoint in ("/auth/me", "/users/public"):
            response = await api_client.get(
                f"{settings.API_V1_STR}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


async def test_access_and_legacy_access_authenticate(
    api_client: httpx.AsyncClient, user_id: uuid.UUID,
) -> None:
    for token in (
        security.create_access_token({"sub": str(user_id), "role": "client"}),
        legacy(user_id, role="client"),
    ):
        response = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json()["id"] == str(user_id)


async def test_access_cannot_be_accepted_by_refresh_even_if_registered(
    api_client: httpx.AsyncClient, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _token: False)
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _token: True)
    for token in (
        security.create_access_token({"sub": str(user_id), "role": "client"}),
        legacy(user_id, role="client"),
    ):
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text


async def test_logout_denies_access_in_refresh_body(
    api_client: httpx.AsyncClient, user_id: uuid.UUID, monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = security.create_access_token({"sub": str(user_id), "role": "client"})
    calls: list[str] = []
    monkeypatch.setattr(auth_router, "delete_refresh_token", lambda _t: calls.append("delete"))
    monkeypatch.setattr(auth_router, "blacklist_token", lambda _t: calls.append("blacklist"))
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"refresh_token": token},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    assert calls == []


async def test_typed_and_legacy_refresh_use_real_disposable_redis(
    api_client: httpx.AsyncClient, user_id: uuid.UUID,
) -> None:
    access = security.create_access_token({"sub": str(user_id), "role": "client"})
    for refresh in (
        security.create_refresh_token({"sub": str(user_id)}),
        legacy(user_id, role=None),
    ):
        store_refresh_token(str(user_id), refresh)
        try:
            minted = await api_client.post(
                f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
            )
            assert minted.status_code == status.HTTP_200_OK, minted.text
            new_access = security.decode_token(minted.json()["access_token"])
            assert new_access is not None and new_access["token_use"] == "access"
            denied = await api_client.get(
                f"{settings.API_V1_STR}/auth/me",
                headers={"Authorization": f"Bearer {refresh}"},
            )
            assert denied.status_code == status.HTTP_401_UNAUTHORIZED
            logged_out = await api_client.post(
                f"{settings.API_V1_STR}/auth/logout",
                headers={"Authorization": f"Bearer {access}"},
                json={"refresh_token": refresh},
            )
            assert logged_out.status_code == status.HTTP_204_NO_CONTENT, logged_out.text
            reused = await api_client.post(
                f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
            )
            assert reused.status_code == status.HTTP_401_UNAUTHORIZED, reused.text
        finally:
            delete_refresh_token(refresh)
            get_redis_client().delete(f"blacklist_token:{refresh}")


def test_token_use_cannot_be_overridden_or_confused() -> None:
    access = security.decode_token(security.create_access_token(
        {"sub": "synthetic", "role": "client", "token_use": "refresh"},
    ))
    refresh = security.decode_token(security.create_refresh_token(
        {"sub": "synthetic", "role": "admin", "token_use": "access"},
    ))
    assert access is not None and access["token_use"] == "access"
    assert refresh is not None and refresh["token_use"] == "refresh"
    assert "role" not in refresh
    assert not security.is_access_token_payload({"sub": "legacy-refresh"})
    assert not security.is_access_token_payload({
        "sub": "signed", "role": "client", "token_use": "unknown",
    })
    assert not security.is_refresh_token_payload({"sub": "signed", "role": "client"})

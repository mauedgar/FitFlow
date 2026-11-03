"""IR014 A10 negotiated pending-token acknowledgement with disposable Redis only."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import httpx
import pytest
from app.core import security
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.enums import UserRole
from app.core.redis_client import get_redis_client
from app.core.token_store import (
    PENDING_SECONDS,
    activate_pending_refresh_token,
    delete_refresh_token,
    is_refresh_token_valid,
    pending_refresh_token_key,
    refresh_token_key,
    store_pending_refresh_token,
)
from app.main import app
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class StubUser:
    id: UUID
    hashed_password: str = "synthetic"
    role: UserRole = UserRole.client
    active: bool = True


async def test_pending_refresh_requires_ack_and_ack_is_idempotent() -> None:
    assert settings.TESTING is True
    user_id = str(uuid4())
    token = security.create_refresh_token({"sub": user_id})
    client = get_redis_client()
    try:
        store_pending_refresh_token(user_id, token)
        assert client.exists(refresh_token_key(token)) == 0
        assert 0 < client.ttl(pending_refresh_token_key(token)) <= PENDING_SECONDS
        assert not is_refresh_token_valid(token)
        assert not activate_pending_refresh_token(str(uuid4()), token)
        assert not is_refresh_token_valid(token)
        assert activate_pending_refresh_token(user_id, token)
        assert activate_pending_refresh_token(user_id, token)  # duplicate/lost ACK response
        assert is_refresh_token_valid(token)
        assert client.exists(pending_refresh_token_key(token)) == 0
    finally:
        delete_refresh_token(token)
        client.close()
    assert not is_refresh_token_valid(token)


async def test_missing_ack_simulates_pending_expiration_without_active_credential() -> None:
    token = security.create_refresh_token({"sub": str(uuid4())})
    client = get_redis_client()
    try:
        payload = security.decode_token(token)
        assert payload is not None
        store_pending_refresh_token(payload["sub"], token)
        client.delete(pending_refresh_token_key(token))  # deterministic TTL expiry
        assert not activate_pending_refresh_token(payload["sub"], token)
        assert not is_refresh_token_valid(token)
    finally:
        delete_refresh_token(token)
        client.close()


async def test_negotiated_login_acks_owner_only_and_legacy_login_is_unchanged(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = StubUser(id=uuid4())
    events: list[str] = []
    async def lookup(*, db: object, email: str) -> StubUser:
        del db, email
        return user
    monkeypatch.setattr(auth_router, "user_get_by_email", lookup)
    monkeypatch.setattr(auth_router.security, "verify_password", lambda *_: True)
    monkeypatch.setattr(auth_router, "store_pending_refresh_token",
                        lambda uid, token: events.append("pending:" + uid))
    monkeypatch.setattr(auth_router, "store_refresh_token",
                        lambda uid, token: events.append("legacy:" + uid))
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda token: False)
    monkeypatch.setattr(auth_router, "activate_pending_refresh_token",
                        lambda uid, token: events.append("ack:" + uid) or True)
    async def owner() -> StubUser:
        return user
    app.dependency_overrides[get_current_user] = owner
    try:
        login = await api_client.post(f"{settings.API_V1_STR}/auth/token",
            data={"username": "synthetic@example.invalid", "password": "fake"},
            headers={"X-FitFlow-Refresh-Ack": "v1"})
        assert login.status_code == 200, login.text
        pair = login.json()
        assert events == ["pending:" + str(user.id)]
        ack = await api_client.post(f"{settings.API_V1_STR}/auth/ack",
            json={"refresh_token": pair["refresh_token"]},
            headers={"Authorization": "Bearer " + pair["access_token"]})
        assert ack.status_code == 204, ack.text
        assert events == ["pending:" + str(user.id), "ack:" + str(user.id)]
        legacy = await api_client.post(f"{settings.API_V1_STR}/auth/token",
            data={"username": "synthetic@example.invalid", "password": "fake"})
        assert legacy.status_code == 200, legacy.text
        assert events[-1] == "legacy:" + str(user.id)
        unsupported = await api_client.post(f"{settings.API_V1_STR}/auth/token",
            data={"username": "synthetic@example.invalid", "password": "fake"},
            headers={"X-FitFlow-Refresh-Ack": "invalid"})
        assert unsupported.status_code == 400
        assert events[-1] == "legacy:" + str(user.id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_ack_denies_wrong_user_before_redis_mutation(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = security.create_refresh_token({"sub": str(uuid4())})
    events: list[str] = []
    async def other_user() -> StubUser:
        return StubUser(id=uuid4())
    app.dependency_overrides[get_current_user] = other_user
    monkeypatch.setattr(auth_router, "activate_pending_refresh_token",
                        lambda uid, t: events.append(uid))
    try:
        response = await api_client.post(f"{settings.API_V1_STR}/auth/ack",
            json={"refresh_token": token})
        assert response.status_code == 403
        assert events == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)

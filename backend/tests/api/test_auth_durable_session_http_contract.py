"""Issue108: HTTP durable session lifecycle on disposable PostgreSQL15."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import delete, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_synthetic_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def release_engine_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def account() -> AsyncIterator[tuple[uuid.UUID, str, str]]:
    subject = uuid.uuid4()
    email = f"durable-login-{subject.hex}@example.com"
    password = "SyntheticModernSession!123"
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=subject, email=email,
            hashed_password=security.get_password_hash(password),
            role=UserRole.client, active=True,
        ))
        await db.commit()
    try:
        yield subject, email, password
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuthSession).where(AuthSession.user_id == subject))
            await db.execute(delete(User).where(User.id == subject))
            await db.commit()


async def new_session(client: httpx.AsyncClient, email: str, password: str) -> tuple[str, str]:
    response = await client.post(
        f"{settings.API_V1_STR}/auth/session/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"], response.json()["refresh_token"]


async def test_durable_login_refresh_logout_idempotence_without_access_bearer(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uid, email, password = account
    monkeypatch.setattr(settings, "REDIS_URL", None)
    access, refresh = await new_session(api_client, email, password)
    a, r = security.decode_token(access), security.decode_token(refresh)
    assert a is not None and r is not None
    assert a["sid"] == r["sid"] and a["sub"] == str(uid)
    assert a["token_use"] == "access" and r["token_use"] == "refresh"
    assert "role" not in r
    before = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert before.status_code == 200, before.text
    renewal = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh",
        json={"refresh_token": refresh},
    )
    assert renewal.status_code == 200, renewal.text
    renewed_access = renewal.json()["access_token"]
    assert security.decode_token(renewed_access)["sid"] == r["sid"]
    # No bearer is supplied: a lost/expired access credential cannot block revoke.
    first = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert first.status_code == 204, first.text
    repeated = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert repeated.status_code == 204, repeated.text
    for bearer in (access, renewed_access):
        blocked = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {bearer}"},
        )
        assert blocked.status_code == 401, blocked.text
    failed_renewal = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh",
        json={"refresh_token": refresh},
    )
    assert failed_renewal.status_code == 401, failed_renewal.text
    await engine.dispose()
    after_new_connection = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert after_new_connection.status_code == 401


async def test_two_modern_logins_are_independent_families(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    _uid, email, password = account
    access_a, refresh_a = await new_session(api_client, email, password)
    access_b, refresh_b = await new_session(api_client, email, password)
    a, b = security.decode_token(access_a), security.decode_token(access_b)
    assert a is not None and b is not None and a["sid"] != b["sid"]
    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh_a},
    )
    assert logout.status_code == 204, logout.text
    denied = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access_a}"},
    )
    assert denied.status_code == 401, denied.text
    still_allowed = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access_b}"},
    )
    assert still_allowed.status_code == 200, still_allowed.text
    refresh_b_response = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh",
        json={"refresh_token": refresh_b},
    )
    assert refresh_b_response.status_code == 200, refresh_b_response.text


async def test_unregistered_modern_jwt_and_legacy_compatibility(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    uid, _email, _password = account
    unregistered_sid = str(uuid.uuid4())
    token = security.create_access_token(
        {"sub": str(uid), "role": "client", "sid": unregistered_sid},
    )
    no_access = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert no_access.status_code == 401
    no_access_other_guard = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/classes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert no_access_other_guard.status_code == 401
    refresh = security.create_refresh_token(
        {"sub": str(uid), "sid": unregistered_sid},
    )
    denied = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh",
        json={"refresh_token": refresh},
    )
    assert denied.status_code == 401
    denied_logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert denied_logout.status_code == 401
    legacy_refresh = security.create_refresh_token({"sub": str(uid)})
    legacy_out = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": legacy_refresh},
    )
    assert legacy_out.status_code == 409
    legacy_access = security.create_access_token({"sub": str(uid), "role": "client"})
    legacy_me = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {legacy_access}"},
    )
    assert legacy_me.status_code == 200


async def test_refresh_resolves_current_database_role_and_inactive_account(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    uid, email, password = account
    _access, refresh = await new_session(api_client, email, password)
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.id == uid).values(role=UserRole.teacher))
        await db.commit()
    updated = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh", json={"refresh_token": refresh},
    )
    assert updated.status_code == 200, updated.text
    assert security.decode_token(updated.json()["access_token"])["role"] == "teacher"
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.id == uid).values(
            deleted_at=datetime.now(tz=UTC), active=True,
        ))
        await db.commit()
    inactive = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh", json={"refresh_token": refresh},
    )
    assert inactive.status_code == 401, inactive.text


async def test_unconfirmed_database_logout_never_returns_204(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    _access, refresh = await new_session(api_client, email, password)
    async def failing_revoke(*_args: object, **_kwargs: object) -> str:
        raise SQLAlchemyError("synthetic lost commit ACK")
    monkeypatch.setattr(auth_router.session_ledger, "revoke", failing_revoke)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 503, response.text

"""Issue108 F01: browser refresh-cookie + CSRF via real ASGI and disposable PG."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core import security, browser_session
from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def only_disposable_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"
    assert settings.BACKEND_CORS_ORIGINS


@pytest.fixture(autouse=True)
async def release_engine_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def account() -> AsyncIterator[tuple[uuid.UUID, str, str]]:
    uid = uuid.uuid4()
    email = f"browser-cookie-{uid.hex}@example.com"
    password = "Cookie-Test-Synthetic-Only!"
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=uid, email=email,
            hashed_password=security.get_password_hash(password),
            role=UserRole.client, active=True,
        ))
        await db.commit()
    try:
        yield uid, email, password
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuthSession).where(AuthSession.user_id == uid))
            await db.execute(delete(User).where(User.id == uid))
            await db.commit()


def origin() -> dict[str, str]:
    return {"Origin": settings.BACKEND_CORS_ORIGINS[0]}


async def login(client: httpx.AsyncClient, email: str, password: str) -> httpx.Response:
    return await client.post(
        f"{settings.API_V1_STR}/auth/browser/token",
        headers=origin(), data={"username": email, "password": password},
    )


async def test_cookie_login_rehydrate_refresh_logout_and_replay_denial(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    monkeypatch.setattr(settings, "REDIS_URL", None)
    response = await login(api_client, email, password)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"access_token", "token_type", "csrf_token"}
    assert len(body["csrf_token"]) == 64
    assert security.decode_token(body["access_token"])["sid"]
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert "path=/api/v1/auth/browser" in cookie
    assert "domain=" not in cookie
    assert response.headers["cache-control"] == "no-store"
    assert browser_session.COOKIE_NAME in api_client.cookies
    boot = await api_client.get(f"{settings.API_V1_STR}/auth/browser/session")
    assert boot.status_code == 200, boot.text
    assert boot.json()["csrf_token"] == body["csrf_token"]
    renewed = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/refresh",
        headers={**origin(), "X-CSRF-Token": body["csrf_token"]},
    )
    assert renewed.status_code == 200, renewed.text
    denied_csrf = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout", headers=origin(),
    )
    assert denied_csrf.status_code == 403
    confirmed = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": body["csrf_token"]},
    )
    assert confirmed.status_code == 204, confirmed.text
    assert "max-age=0" in confirmed.headers["set-cookie"].lower()
    protected = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert protected.status_code == 401, protected.text
    refresh_after = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/refresh",
        headers={**origin(), "X-CSRF-Token": body["csrf_token"]},
    )
    assert refresh_after.status_code == 401


async def test_cookie_csrf_origin_forgery_and_header_mismatch_rejected(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    _uid, email, password = account
    bad_origin = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/token",
        data={"username": email, "password": password},
        headers={"Origin": "https://evil.example.org"},
    )
    assert bad_origin.status_code == 403
    logged = await login(api_client, email, password)
    assert logged.status_code == 200, logged.text
    csrf = logged.json()["csrf_token"]
    for h in (
        {},
        {"Origin": "https://evil.example.org", "X-CSRF-Token": csrf},
        {**origin(), "X-CSRF-Token": "0" * 64},
        {**origin(), "Sec-Fetch-Site": "cross-site", "X-CSRF-Token": csrf},
    ):
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/browser/logout", headers=h,
        )
        assert response.status_code == 403, response.text
    still_live = await api_client.get(
        f"{settings.API_V1_STR}/auth/browser/session",
    )
    assert still_live.status_code == 200, still_live.text


async def test_unconfirmed_browser_logout_keeps_cookie_and_never_reports_204(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    logged = await login(api_client, email, password)
    assert logged.status_code == 200, logged.text
    csrf = logged.json()["csrf_token"]
    async def cannot_confirm(*_a: object, **_kw: object) -> str:
        raise SQLAlchemyError("synthetic PostgreSQL unavailable")
    monkeypatch.setattr(auth_router.session_ledger, "revoke", cannot_confirm)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": csrf},
    )
    assert response.status_code == 503
    assert "set-cookie" not in response.headers
    assert browser_session.COOKIE_NAME in api_client.cookies


async def test_cookie_secure_flag_required_outside_local_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi import Response
    monkeypatch.setattr(settings, "ENV", "production")
    response = Response()
    token = security.create_refresh_token({
        "sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()),
    })
    browser_session.set_refresh_cookie(response, token)
    cookie = response.headers["set-cookie"].lower()
    assert "secure" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


async def test_second_browser_login_must_not_replace_active_cookie_family(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    """An unrevoked family cannot lose its sole HttpOnly refresh proof."""
    _uid, email, password = account
    first = await login(api_client, email, password)
    assert first.status_code == 200, first.text
    csrf = first.json()["csrf_token"]

    replacement = await login(api_client, email, password)
    assert replacement.status_code == 409, replacement.text
    assert "revocación" in replacement.json()["detail"]
    still_active = await api_client.get(
        f"{settings.API_V1_STR}/auth/browser/session",
    )
    assert still_active.status_code == 200, still_active.text
    assert still_active.json()["csrf_token"] == csrf

    confirmed = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": csrf},
    )
    assert confirmed.status_code == 204, confirmed.text
    reauthenticated = await login(api_client, email, password)
    assert reauthenticated.status_code == 200, reauthenticated.text
    assert reauthenticated.json()["csrf_token"] != csrf

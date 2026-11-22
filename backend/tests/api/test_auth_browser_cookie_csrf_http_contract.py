"""Issue108 F01: browser refresh-cookie + CSRF via real ASGI and disposable PG."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from jose import jwt
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.core import security, browser_session
from auth_session_test_helpers import require_local_test_database
from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def only_disposable_database() -> None:
    require_local_test_database()
    if not settings.BACKEND_CORS_ORIGINS:
        raise RuntimeError("BLOCKED_PRECONDITION: synthetic browser Origin required")


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
    boot = await api_client.get(
        f"{settings.API_V1_STR}/auth/browser/session", headers=origin(),
    )
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
        headers=origin(),
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
        headers=origin(),
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


async def test_cookie_postcommit_recovery_proof_preserves_idempotent_logout(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lost ACK must not let login overwrite the remaining cookie proof."""
    _uid, email, password = account
    login_response = await login(api_client, email, password)
    assert login_response.status_code == 200, login_response.text
    csrf = login_response.json()["csrf_token"]
    original = auth_router.session_ledger.revoke

    async def commit_then_lose_ack(db: object, *, refresh_token: str) -> str:
        result = await original(db, refresh_token=refresh_token)
        assert result == "COMMITTED"
        raise ConnectionError("synthetic lost ACK after PostgreSQL commit")

    monkeypatch.setattr(auth_router.session_ledger, "revoke", commit_then_lose_ack)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": csrf},
    )
    assert response.status_code == 503, response.text
    assert "set-cookie" not in response.headers
    denied = await login(api_client, email, password)
    assert denied.status_code == 409, denied.text
    assert "set-cookie" not in denied.headers

    proof = await api_client.get(
        f"{settings.API_V1_STR}/auth/browser/logout-proof",
        headers=origin(),
    )
    assert proof.status_code == 200, proof.text
    assert proof.json() == {"csrf_token": csrf}
    assert proof.headers.get("Cache-Control") == "no-store"
    assert "access_token" not in proof.text

    monkeypatch.setattr(auth_router.session_ledger, "revoke", original)
    replay = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": proof.json()["csrf_token"]},
    )
    assert replay.status_code == 204, replay.text
    assert "max-age=0" in replay.headers["set-cookie"].lower()
    restarted = await login(api_client, email, password)
    assert restarted.status_code == 200, restarted.text


async def test_cookie_existing_active_family_cannot_be_replaced(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    """The first family remains durably authoritative until explicit logout."""
    _uid, email, password = account
    first = await login(api_client, email, password)
    assert first.status_code == 200, first.text
    csrf = first.json()["csrf_token"]
    conflict = await login(api_client, email, password)
    assert conflict.status_code == 409, conflict.text
    assert "set-cookie" not in conflict.headers
    assert (await api_client.get(
        f"{settings.API_V1_STR}/auth/browser/session", headers=origin(),
    )).status_code == 200
    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/browser/logout",
        headers={**origin(), "X-CSRF-Token": csrf},
    )
    assert logout.status_code == 204, logout.text
    new_login = await login(api_client, email, password)
    assert new_login.status_code == 200, new_login.text


async def test_browser_credential_reads_fail_closed_without_trusted_origin(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    """No access bearer or CSRF proof for untrusted browser reads."""
    _uid, email, password = account
    logged = await login(api_client, email, password)
    assert logged.status_code == 200, logged.text
    for suffix in ("/session", "/logout-proof"):
        path = f"{settings.API_V1_STR}/auth/browser{suffix}"
        denied_headers = (
            {},
            {"Origin": "https://evil.example.org"},
            {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "cors"},
            {"Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors"},
            {"Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate"},
            {**origin(), "Sec-Fetch-Site": "cross-site"},
        )
        for headers in denied_headers:
            denied = await api_client.get(path, headers=headers)
            assert denied.status_code == 403, (suffix, headers, denied.text)
            assert "access_token" not in denied.text
            assert "csrf_token" not in denied.text
        trusted = await api_client.get(path, headers=origin())
        assert trusted.status_code == 200, trusted.text
        assert trusted.headers["Cache-Control"] == "no-store"
        vary_tokens = {part.strip().lower() for part in trusted.headers["Vary"].split(",")}
        assert "origin" in vary_tokens
        same_origin = await api_client.get(path, headers={
            "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "cors",
        })
        assert same_origin.status_code == 200, same_origin.text



async def test_expired_signed_cookie_does_not_overwrite_unresolved_logout_family(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    """An anomalously still-present expired signed cookie is not an ACK.

    Real browsers evict at Max-Age; this forces the edge case explicitly
    so the server never issues another family while signed proof remains.
    """
    uid, email, password = account
    expired = jwt.encode(
        {
            "sub": str(uid), "sid": str(uuid.uuid4()),
            "token_use": "refresh",
            "exp": int((datetime.now(tz=UTC) - timedelta(seconds=35)).timestamp()),
        },
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    api_client.cookies.set(
        browser_session.COOKIE_NAME, expired, path=browser_session.COOKIE_PATH,
    )
    denied = await login(api_client, email, password)
    assert denied.status_code == 409, denied.text
    assert "access_token" not in denied.text
    assert "set-cookie" not in denied.headers
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(AuthSession).where(AuthSession.user_id == uid)
        )
        assert existing is None, "No PG family may be minted behind the stale cookie"
    # A browser which has actually expired its cookie can authenticate anew;
    # the server never reports the previous logout as confirmed.
    api_client.cookies.clear()
    admitted = await login(api_client, email, password)
    assert admitted.status_code == 200, admitted.text

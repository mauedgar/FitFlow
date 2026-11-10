"""A03 signed session revocation over real disposable PostgreSQL15/Redis7."""
from __future__ import annotations

import uuid
from datetime import timedelta
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import status
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.core import security, session_revocation
from app.core.config import settings
from app.core.enums import UserRole
from app.core.redis_client import get_redis_client
from app.core.token_keys import opaque_jwt_key
from app.core.token_store import delete_refresh_token, store_refresh_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.services.errors import ExternalServiceError

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_disposable_database() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def admin_user() -> AsyncIterator[tuple[uuid.UUID, str, str]]:
    subject = uuid.uuid4()
    email = f"session-{subject.hex}@example.com"
    password = "SyntheticSessionOnly!42"
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=subject, email=email,
            hashed_password=security.get_password_hash(password),
            role=UserRole.admin, active=True,
        ))
        await db.commit()
    try:
        yield subject, email, password
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == subject))
            await db.commit()


def pair(subject: uuid.UUID, sid: str) -> tuple[str, str]:
    return (
        security.create_access_token({"sub": str(subject), "role": "admin", "sid": sid}),
        security.create_refresh_token({"sub": str(subject), "sid": sid}),
    )


def clean_session(sid: str, refresh: str) -> None:
    client = get_redis_client()
    delete_refresh_token(refresh)
    client.delete(session_revocation._revocation_key(uuid.UUID(sid).hex))
    client.delete(opaque_jwt_key("blacklist_token:", refresh))


async def test_login_refresh_and_logout_revoke_entire_signed_session(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject, email, password = admin_user
    login = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert login.status_code == status.HTTP_200_OK, login.text
    access = login.json()["access_token"]
    refresh = login.json()["refresh_token"]
    access_data = security.decode_token(access)
    refresh_data = security.decode_token(refresh)
    assert access_data is not None and refresh_data is not None
    sid = access_data["sid"]
    assert access_data["token_use"] == "access"
    assert refresh_data["token_use"] == "refresh"
    assert sid == refresh_data["sid"]
    try:
        headers = {"Authorization": f"Bearer {access}"}
        before = await api_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert before.status_code == 200, before.text
        admin_before = await api_client.get(
            f"{settings.API_V1_STR}/users/public", headers=headers,
        )
        assert admin_before.status_code == 200, admin_before.text
        renewed = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
        )
        assert renewed.status_code == 200, renewed.text
        renewed_access = renewed.json()["access_token"]
        renewed_data = security.decode_token(renewed_access)
        assert renewed_data is not None and renewed_data["sid"] == sid

        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers=headers, json={"refresh_token": refresh},
        )
        assert logout.status_code == 204, logout.text
        assert get_redis_client().ttl(session_revocation._revocation_key(sid.replace("-", ""))) > 0
        for revoked_access in (access, renewed_access):
            revoked_headers = {"Authorization": f"Bearer {revoked_access}"}
            for endpoint in ("/auth/me", "/users/public"):
                denied = await api_client.get(
                    f"{settings.API_V1_STR}{endpoint}", headers=revoked_headers,
                )
                assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text
        cannot_refresh = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
        )
        assert cannot_refresh.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        clean_session(sid, refresh)


async def test_one_session_logout_cannot_revoke_a_different_session(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    sid_a, sid_b = str(uuid.uuid4()), str(uuid.uuid4())
    access_a, refresh_a = pair(subject, sid_a)
    _, refresh_b = pair(subject, sid_b)
    store_refresh_token(str(subject), refresh_a)
    store_refresh_token(str(subject), refresh_b)
    try:
        mismatch = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {access_a}"},
            json={"refresh_token": refresh_b},
        )
        assert mismatch.status_code == status.HTTP_403_FORBIDDEN, mismatch.text
        still_active = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access_a}"},
        )
        assert still_active.status_code == 200
        assert get_redis_client().exists(session_revocation._revocation_key(sid_a.replace("-", ""))) == 0
    finally:
        clean_session(sid_a, refresh_a)
        clean_session(sid_b, refresh_b)


async def test_redis_outage_fails_closed_for_both_bearer_pipelines(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, _ = pair(subject, sid)

    def unavailable() -> None:
        raise ExternalServiceError("Redis no está disponible.")

    monkeypatch.setattr(session_revocation, "get_redis_client", unavailable)
    for endpoint in ("/auth/me", "/users/public"):
        response = await api_client.get(
            f"{settings.API_V1_STR}{endpoint}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, response.text


async def test_legacy_logout_blacklists_presented_access_credential(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    legacy_access = security.create_access_token({"sub": str(subject), "role": "admin"})
    legacy_refresh = security.create_refresh_token({"sub": str(subject)})
    store_refresh_token(str(subject), legacy_refresh)
    try:
        headers = {"Authorization": f"Bearer {legacy_access}"}
        before = await api_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert before.status_code == 200, before.text
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers=headers, json={"refresh_token": legacy_refresh},
        )
        assert response.status_code == 204, response.text
        denied = await api_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert denied.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        delete_refresh_token(legacy_refresh)
        get_redis_client().delete(opaque_jwt_key("blacklist_token:", legacy_refresh))
        get_redis_client().delete(opaque_jwt_key("blacklist_token:", legacy_access))



async def test_expired_access_can_still_revoke_registered_signed_session(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    expired_access = security.create_access_token(
        {"sub": str(subject), "role": "admin", "sid": sid},
        expires_delta=timedelta(seconds=-5),
    )
    still_valid_access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)
    try:
        expired_check = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {expired_access}"},
        )
        assert expired_check.status_code == status.HTTP_401_UNAUTHORIZED
        before = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {still_valid_access}"},
        )
        assert before.status_code == status.HTTP_200_OK, before.text
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {expired_access}"},
            json={"refresh_token": refresh},
        )
        assert logout.status_code == status.HTTP_204_NO_CONTENT, logout.text
        denied = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {still_valid_access}"},
        )
        assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text
        reused = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert reused.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        clean_session(sid, refresh)


async def test_refresh_only_logout_requires_registration_and_revokes_session(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, refresh = pair(subject, sid)
    unregistered = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": refresh},
    )
    assert unregistered.status_code == status.HTTP_401_UNAUTHORIZED
    assert get_redis_client().exists(
        session_revocation._revocation_key(sid.replace("-", ""))
    ) == 0
    store_refresh_token(str(subject), refresh)
    try:
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": refresh},
        )
        assert logout.status_code == status.HTTP_204_NO_CONTENT, logout.text
        after = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert after.status_code == status.HTTP_401_UNAUTHORIZED, after.text
    finally:
        clean_session(sid, refresh)


async def test_refresh_only_logout_redis_outage_returns_503_without_false_success(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, refresh = pair(admin_user[0], str(uuid.uuid4()))

    def unavailable(_token: str) -> bool:
        raise ExternalServiceError("Redis no está disponible.")

    from app.routers import auth as auth_router
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", unavailable)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": refresh},
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


async def test_logout_marker_outlives_refresh_expiry_on_both_bearer_pipelines(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a just-refreshed access after the *old* refresh marker would expire."""
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    _access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)

    class ExpiringSidRedis:
        def __init__(self) -> None:
            self.now = 0
            self.deadlines: dict[str, int] = {}

        def set(self, key: str, _value: str, *, ex: int) -> None:
            self.deadlines[key] = self.now + ex

        def exists(self, key: str) -> int:
            return int(self.now < self.deadlines.get(key, 0))

    fake = ExpiringSidRedis()
    monkeypatch.setattr(session_revocation, "get_redis_client", lambda: fake)
    try:
        newly_minted = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert newly_minted.status_code == status.HTTP_200_OK, newly_minted.text
        access = newly_minted.json()["access_token"]
        assert security.decode_token(access)["sid"] == sid

        # Simulate a refresh credential at the final second of its lifetime.
        # The real signed token remains valid while API requests complete.
        monkeypatch.setattr(
            session_revocation, "token_seconds_until_expiry", lambda _token: 1,
        )
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": refresh},
        )
        assert logout.status_code == status.HTTP_204_NO_CONTENT, logout.text
        marker = session_revocation._revocation_key(uuid.UUID(sid).hex)
        assert fake.deadlines[marker] > settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Advancing Redis logical time exposes premature marker expiry without
        # a slow/flaky real-time sleep or altering JWT signature expiration.
        fake.now = 2
        assert fake.exists(marker) == 1
        assert security.decode_token(access) is not None
        for endpoint in ("/auth/me", "/users/public"):
            denied = await api_client.get(
                f"{settings.API_V1_STR}{endpoint}",
                headers={"Authorization": f"Bearer {access}"},
            )
            assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text
    finally:
        clean_session(sid, refresh)

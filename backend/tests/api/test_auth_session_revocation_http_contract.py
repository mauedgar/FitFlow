"""A03 signed session revocation over real disposable PostgreSQL15/Redis7."""
from __future__ import annotations

import uuid
from datetime import timedelta
from collections.abc import AsyncIterator

import httpx
import pytest
from redis.exceptions import RedisError
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
    client.delete(opaque_jwt_key("logout_confirmed:", refresh))


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
        get_redis_client().delete(opaque_jwt_key("logout_confirmed:", legacy_refresh))
        get_redis_client().delete(opaque_jwt_key("blacklist_token:", legacy_access))
        get_redis_client().delete(session_revocation._legacy_subject_revocation_key(str(subject)))



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

    def unavailable(*_args: object, **_kwargs: object) -> bool:
        raise ExternalServiceError("Redis no está disponible.")

    from app.routers import auth as auth_router
    monkeypatch.setattr(auth_router, "commit_logout", unavailable)
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

        def eval(self, _script: str, numkeys: int, *args: object) -> int:
            # One additional subject-wide legacy key was added to the atomic
            # Redis contract; SID sessions still write only their own marker.
            assert numkeys == 8
            keys = args[:numkeys]
            arguments = args[numkeys:]
            assert arguments[1] == "sid"
            assert int(arguments[6]) > int(arguments[2])
            self.set(str(keys[4]), "1", ex=int(arguments[2]))
            return 1

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


async def test_repeated_sid_logout_ack_is_idempotent_and_access_remains_revoked(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)
    try:
        headers = {"Authorization": f"Bearer {access}"}
        first = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": refresh}, headers=headers,
        )
        second = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            json={"refresh_token": refresh}, headers=headers,
        )
        assert first.status_code == second.status_code == 204
        assert get_redis_client().exists(opaque_jwt_key("logout_confirmed:", refresh)) == 1
        denied = await api_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert denied.status_code == 401
        rejected_refresh = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
        )
        assert rejected_refresh.status_code == 401
    finally:
        clean_session(sid, refresh)


async def test_legacy_logout_ack_is_idempotent_and_blacklists_presented_access(
    api_client: httpx.AsyncClient, admin_user: tuple[uuid.UUID, str, str],
) -> None:
    subject = admin_user[0]
    access = security.create_access_token({"sub": str(subject), "role": "admin"})
    refresh = security.create_refresh_token({"sub": str(subject)})
    store_refresh_token(str(subject), refresh)
    headers = {"Authorization": f"Bearer {access}"}
    try:
        first = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh}, headers=headers,
        )
        second = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh}, headers=headers,
        )
        assert first.status_code == second.status_code == 204
        assert get_redis_client().exists(opaque_jwt_key("logout_confirmed:", refresh)) == 1
        assert get_redis_client().exists(opaque_jwt_key("blacklist_token:", access)) == 1
        denied = await api_client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
        assert denied.status_code == 401
    finally:
        delete_refresh_token(refresh)
        client = get_redis_client()
        client.delete(opaque_jwt_key("logout_confirmed:", refresh))
        client.delete(opaque_jwt_key("blacklist_token:", refresh))
        client.delete(opaque_jwt_key("blacklist_token:", access))
        client.delete(session_revocation._legacy_subject_revocation_key(str(subject)))


async def test_redis_unavailable_before_atomic_commit_does_not_revoke_or_ack(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)
    try:
        def unavailable() -> None:
            raise ExternalServiceError("Redis no está disponible.")

        with monkeypatch.context() as temporary:
            temporary.setattr(session_revocation, "get_redis_client", unavailable)
            failed = await api_client.post(
                f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
            )
        assert failed.status_code == 503
        assert get_redis_client().exists(opaque_jwt_key("logout_confirmed:", refresh)) == 0
        still_active = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert still_active.status_code == 200
        restored = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
        )
        assert restored.status_code == 204
    finally:
        clean_session(sid, refresh)

async def test_redis_commit_ack_lost_after_actual_write_recovers_on_signed_retry(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A real disposable Redis commit with a lost client ACK is 503 then 204."""
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)
    redis_client = get_redis_client()

    class AckLost:
        def eval(self, *args: object) -> int:
            assert redis_client.eval(*args) == 1
            raise RedisError("synthetic acknowledgement lost")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(session_revocation, "get_redis_client", lambda: AckLost())
            failed = await api_client.post(
                f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
            )
        assert failed.status_code == 503
        assert redis_client.exists(opaque_jwt_key("logout_confirmed:", refresh)) == 1
        retry = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
        )
        assert retry.status_code == 204
        denied = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert denied.status_code == 401
    finally:
        clean_session(sid, refresh)


async def test_real_disposable_redis_post_first_write_fault_remains_unconfirmed(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fault-injected Lua is a synthetic variant, not the shipped script."""
    subject = admin_user[0]
    sid = str(uuid.uuid4())
    access, refresh = pair(subject, sid)
    store_refresh_token(str(subject), refresh)
    redis_client = get_redis_client()
    original_script = session_revocation._LOGOUT_SCRIPT
    first = "  redis.call('SET', KEYS[5], '1', 'EX', ARGV[3])"
    assert original_script.count(first) == 1
    broken_script = original_script.replace(
        first, first + "\n  return redis.error_reply('synthetic after sid write')",
    )
    try:
        with monkeypatch.context() as patch:
            patch.setattr(session_revocation, "_LOGOUT_SCRIPT", broken_script)
            failed = await api_client.post(
                f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
            )
        assert failed.status_code == 503
        marker = session_revocation._revocation_key(uuid.UUID(sid).hex)
        assert redis_client.exists(marker) == 1
        assert redis_client.exists(opaque_jwt_key("logout_confirmed:", refresh)) == 0
        denied = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert denied.status_code == 401
        retry = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout", json={"refresh_token": refresh},
        )
        assert retry.status_code == 204
    finally:
        clean_session(sid, refresh)


async def test_sidless_logout_revokes_all_legacy_access_and_refresh_for_subject(
    api_client: httpx.AsyncClient,
    admin_user: tuple[uuid.UUID, str, str],
) -> None:
    """A SID-less logout fails closed for every legacy credential of the account."""
    subject = admin_user[0]
    access_a = security.create_access_token({
        "sub": str(subject), "role": "admin", "jti": uuid.uuid4().hex,
    })
    access_b = security.create_access_token({
        "sub": str(subject), "role": "admin", "jti": uuid.uuid4().hex,
    })
    refresh = security.create_refresh_token({"sub": str(subject)})
    assert access_a != access_b
    another_refresh = security.create_refresh_token({"sub": str(subject), "jti": uuid.uuid4().hex})
    signed_sid = str(uuid.uuid4())
    independent_new_session = security.create_access_token({
        "sub": str(subject), "role": "admin", "sid": signed_sid,
    })
    store_refresh_token(str(subject), refresh)
    store_refresh_token(str(subject), another_refresh)
    client = get_redis_client()
    try:
        for bearer in (access_a, access_b):
            before = await api_client.get(
                f"{settings.API_V1_STR}/auth/me",
                headers={"Authorization": f"Bearer {bearer}"},
            )
            assert before.status_code == 200
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {access_a}"},
            json={"refresh_token": refresh},
        )
        assert logout.status_code == 204
        denied = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access_a}"},
        )
        assert denied.status_code == 401
        residual = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {access_b}"},
        )
        assert residual.status_code == 401
        marker = session_revocation._legacy_subject_revocation_key(str(subject))
        assert client.ttl(marker) > settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        assert client.exists(opaque_jwt_key("logout_confirmed:", refresh)) == 1
        still_valid_new_session = await api_client.get(
            f"{settings.API_V1_STR}/auth/me",
            headers={"Authorization": f"Bearer {independent_new_session}"},
        )
        assert still_valid_new_session.status_code == 200
        second_legacy_refresh = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": another_refresh},
        )
        assert second_legacy_refresh.status_code == 401
        reuse = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
        )
        assert reuse.status_code == 401
    finally:
        delete_refresh_token(refresh)
        delete_refresh_token(another_refresh)
        for bearer in (access_a, access_b, refresh):
            client.delete(opaque_jwt_key("blacklist_token:", bearer))
        client.delete(opaque_jwt_key("logout_confirmed:", refresh))
        client.delete(session_revocation._legacy_subject_revocation_key(str(subject)))


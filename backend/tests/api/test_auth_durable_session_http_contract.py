"""Issue108: HTTP durable session lifecycle on disposable PostgreSQL15."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from jose import jwt

import httpx
import pytest
from sqlalchemy import delete, update
from auth_session_test_helpers import require_local_test_database
from sqlalchemy.exc import SQLAlchemyError

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
from app.crud.auth_session import fingerprint
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def require_synthetic_database() -> None:
    require_local_test_database()


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
    assert legacy_me.status_code == 401


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



async def test_unknown_register_commit_outcome_never_returns_token_pair(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    real_register = auth_router.session_ledger.register

    async def committed_but_no_response(db: object, *, subject: uuid.UUID, refresh_token: str):
        await real_register(db, subject=subject, refresh_token=refresh_token)
        raise ConnectionError("synthetic connection lost after registration COMMIT")

    monkeypatch.setattr(auth_router.session_ledger, "register", committed_but_no_response)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 503, response.text
    assert "access_token" not in response.text
    assert "refresh_token" not in response.text


async def test_unknown_logout_ack_after_real_commit_reconciles_on_exact_replay(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    access, refresh = await new_session(api_client, email, password)
    real_revoke = auth_router.session_ledger.revoke

    async def committed_but_ack_lost(db: object, *, refresh_token: str) -> str:
        result = await real_revoke(db, refresh_token=refresh_token)
        assert result == "COMMITTED"
        raise ConnectionError("synthetic network ACK lost after COMMIT")

    monkeypatch.setattr(auth_router.session_ledger, "revoke", committed_but_ack_lost)
    first = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert first.status_code == 503, first.text
    monkeypatch.setattr(auth_router.session_ledger, "revoke", real_revoke)
    await engine.dispose()
    exact_replay = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert exact_replay.status_code == 204, exact_replay.text
    denied = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert denied.status_code == 401, denied.text


async def test_unexpected_logout_exception_is_controlled_503(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _uid, email, password = account
    _access, refresh = await new_session(api_client, email, password)

    async def unexpected(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("synthetic transaction finalization error")

    monkeypatch.setattr(auth_router.session_ledger, "revoke", unexpected)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "Revocación durable no confirmada."


async def test_default_token_and_legacy_refresh_url_route_modern_sid_through_pg(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The original API paths must not reintroduce SID-less issuance or Redis dependency."""
    subject, email, password = account
    monkeypatch.setattr(settings, "REDIS_URL", None)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    pair = response.json()
    access = security.decode_token(pair["access_token"])
    refresh = security.decode_token(pair["refresh_token"])
    assert access is not None and refresh is not None
    assert access["sid"] == refresh["sid"]
    assert access["sub"] == str(subject)
    assert refresh["token_use"] == "refresh" and "role" not in refresh
    renewed = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    assert renewed.status_code == 200, renewed.text
    renewed_claims = security.decode_token(renewed.json()["access_token"])
    assert renewed_claims is not None and renewed_claims["sid"] == access["sid"]
    logout = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {pair['access_token']}"},
        json={"refresh_token": pair["refresh_token"]},
    )
    assert logout.status_code == 204, logout.text
    blocked = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {pair['access_token']}"},
    )
    assert blocked.status_code == 401
    replay = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    assert replay.status_code == 401


async def test_expired_signed_refresh_exact_ack_only_after_pg_commit(
    api_client: httpx.AsyncClient, account: tuple[uuid.UUID, str, str],
) -> None:
    """Expired token cannot revoke active family; exact committed replay is 204."""
    uid, _email, _password = account
    expired = datetime.now(tz=UTC) - timedelta(seconds=45)
    revoked_sid, active_sid = uuid.uuid4(), uuid.uuid4()
    def signed(sid: uuid.UUID) -> str:
        return jwt.encode(
            {"sub": str(uid), "sid": str(sid), "token_use": "refresh",
             "exp": int(expired.timestamp())},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM,
        )
    revoked_token, active_token = signed(revoked_sid), signed(active_sid)
    async with AsyncSessionLocal() as db:
        db.add_all([
            AuthSession(id=revoked_sid, user_id=uid,
                        refresh_digest=fingerprint(revoked_token),
                        expires_at=expired, revoked_at=expired),
            AuthSession(id=active_sid, user_id=uid,
                        refresh_digest=fingerprint(active_token),
                        expires_at=expired),
        ])
        await db.commit()
    confirmed = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": revoked_token},
    )
    assert confirmed.status_code == 204, confirmed.text
    blocked = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/logout",
        json={"refresh_token": active_token},
    )
    assert blocked.status_code == 401, blocked.text
    renewed = await api_client.post(
        f"{settings.API_V1_STR}/auth/session/refresh",
        json={"refresh_token": revoked_token},
    )
    assert renewed.status_code == 401, renewed.text
    async with AsyncSessionLocal() as db:
        unchanged = await db.get(AuthSession, active_sid)
        assert unchanged is not None and unchanged.revoked_at is None

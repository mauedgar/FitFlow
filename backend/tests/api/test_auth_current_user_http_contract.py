"""HTTP contract for access-token subject and current-user resolution."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from jose import jwt
from fastapi import status
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import make_url

from app.core import security, deps as auth_deps
from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from app.routers import auth as auth_router

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    """Fail closed unless this Auth contract uses fitflow_test."""
    target = make_url(settings.DATABASE_URL)
    if (
        target.database != "fitflow_test"
        or (target.host or "").lower() not in {"127.0.0.1", "localhost", "::1"}
        or settings.ENV != "test"
        or not settings.TESTING
    ):
        raise RuntimeError(
            "Auth current-user HTTP contract requires local fitflow_test "
            "with ENV=test and TESTING=true before writing fixtures."
        )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    """Dispose pooled database connections after each HTTP contract test."""
    yield
    await engine.dispose()


@pytest.fixture
async def persisted_auth_user() -> AsyncIterator[tuple[uuid.UUID, str, str]]:
    """Create one real active User and hard-remove it after the test."""
    user_id = uuid.uuid4()
    marker = uuid.uuid4().hex
    email = f"auth-current-user-{marker}@example.com"
    password = "FitFlowAuthContract!42"

    async with AsyncSessionLocal() as db:
        db.add(
            User(
                id=user_id,
                email=email,
                hashed_password=security.get_password_hash(password),
                role=UserRole.client,
                active=True,
            )
        )
        await db.commit()

    try:
        yield user_id, email, password
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()


async def test_login_access_token_subject_resolves_same_user_through_me(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
) -> None:
    """Prove /auth/token persists a modern signed SID before /auth/me."""
    user_id, email, password = persisted_auth_user

    login_response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )

    assert login_response.status_code == status.HTTP_200_OK, login_response.text

    token_pair = login_response.json()
    assert token_pair["access_token"]
    assert token_pair["refresh_token"]

    access_token = token_pair["access_token"]
    payload = security.decode_token(access_token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["role"] == UserRole.client.value
    assert isinstance(payload.get("sid"), str) and payload["sid"]
    refresh_payload = security.decode_token(token_pair["refresh_token"])
    assert refresh_payload is not None
    assert refresh_payload["sid"] == payload["sid"]
    async with AsyncSessionLocal() as db:
        record = await db.get(AuthSession, uuid.UUID(payload["sid"]))
        assert record is not None and record.user_id == user_id
        assert record.revoked_at is None

    me_response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == status.HTTP_200_OK, me_response.text

    body = me_response.json()
    assert body["id"] == str(user_id)
    assert body["email"] == email
    assert body["role"] == UserRole.client.value
    assert body["active"] is True


async def test_me_without_bearer_token_preserves_framework_auth_failure(
    api_client: httpx.AsyncClient,
) -> None:
    """Observe and assert the current missing-bearer contract."""
    response = await api_client.get(f"{settings.API_V1_STR}/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_me_with_invalid_token_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    """Invalid token syntax remains a bounded authentication failure."""
    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "Bearer definitely-not-a-jwt"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Token inválido o expirado"}
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_me_with_expired_token_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    """Expired signed access tokens remain bounded as HTTP 401."""
    token = security.create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "role": UserRole.client.value,
        },
        expires_delta=timedelta(seconds=-1),
    )

    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Token inválido o expirado"}


async def test_me_with_signed_non_uuid_subject_never_returns_500(
    api_client: httpx.AsyncClient,
) -> None:
    """A signed non-UUID subject is rejected before primary-key lookup."""
    token = security.create_access_token(
        data={
            "sub": "not-a-user-uuid",
            "role": UserRole.client.value,
        }
    )

    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Token inválido o expirado"}



async def test_me_with_unregistered_modern_family_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    """A signed bearer never reaches User lookup without a live PG family."""
    missing_user_id = uuid.uuid4()
    token = security.create_access_token({
        "sub": str(missing_user_id),
        "role": UserRole.client.value,
        "sid": str(uuid.uuid4()),
    })
    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Sesión no registrada o revocada."}

async def test_refresh_registered_token_returns_access_token_with_same_user_id_subject(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
) -> None:
    """The old API URL serves a real registered PostgreSQL session."""
    uid, email, password = persisted_auth_user
    logged = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert logged.status_code == status.HTTP_200_OK, logged.text
    refreshed = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": logged.json()["refresh_token"]},
    )
    assert refreshed.status_code == status.HTTP_200_OK, refreshed.text
    payload = security.decode_token(refreshed.json()["access_token"])
    assert payload is not None
    assert payload["sub"] == str(uid)
    original = security.decode_token(logged.json()["refresh_token"])
    assert original is not None
    assert payload["sid"] == original["sid"]


async def test_refresh_with_malformed_token_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "definitely-not-a-jwt"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.request.url.query == b""
    assert "definitely-not-a-jwt" not in response.text
    assert response.json() == {"detail": "Refresh de sesión inválido."}


async def test_refresh_with_expired_token_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    expired = security.create_access_token(
        {"sub": str(uuid.uuid4())}, expires_delta=timedelta(seconds=-1)
    )
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": expired},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh de sesión inválido."}


async def test_refresh_with_unregistered_token_returns_401(
    api_client: httpx.AsyncClient,
) -> None:
    refresh = security.create_refresh_token({
        "sub": str(uuid.uuid4()), "sid": str(uuid.uuid4()),
    })
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": refresh},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Sesión no registrada o revocada."}


async def test_redis_blacklist_cannot_authorize_sidless_refresh(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    signed = security.create_refresh_token({"sub": str(uuid.uuid4())})
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _token: False)
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _token: True)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": signed},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh de sesión inválido."}


async def test_sidless_refresh_never_consults_blacklist_when_redis_fails(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_token: str) -> bool:
        raise AssertionError("Redis blacklist must not be consulted")
    monkeypatch.setattr(auth_router, "is_token_blacklisted", unavailable)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": "opaque-refresh-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh de sesión inválido."}


async def test_sidless_refresh_never_consults_redis_registry(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    signed = security.create_refresh_token({"sub": str(uuid.uuid4())})
    def unavailable(_token: str) -> bool:
        raise AssertionError("Redis registry must not be consulted")
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", unavailable)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": signed},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh de sesión inválido."}

async def test_refresh_rejects_query_only_refresh_token_transport(
    api_client: httpx.AsyncClient,
) -> None:
    query_token = "r008-query-token-must-not-be-consumed"
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        params={"refresh_token": query_token},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert query_token not in response.text



async def test_legacy_refresh_cannot_mint_access_even_before_original_expiration(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
) -> None:
    uid, _email, _password = persisted_auth_user
    expires = int((datetime.now(tz=UTC) + timedelta(seconds=105)).timestamp())
    untyped = jwt.encode(
        {"sub": str(uid), "exp": expires},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    typed = security.create_refresh_token({"sub": str(uid)})
    for signed in (untyped, typed):
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": signed},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access_token" not in response.text




async def test_current_user_final_pg_lookup_error_returns_503(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An outage after the SID check is still persistence-unavailable."""
    _uid, email, password = persisted_auth_user
    logged = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert logged.status_code == 200, logged.text
    access = logged.json()["access_token"]

    async def unavailable(*_args: object, **_kwargs: object) -> None:
        raise SQLAlchemyError("synthetic user lookup failure")

    monkeypatch.setattr(auth_deps.user_crud, "get", unavailable)
    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 503, response.text
    assert response.json() == {"detail": "Persistencia de sesiones no disponible."}


@pytest.mark.parametrize("principal_state", ["missing", "inactive", "deleted"])
async def test_registered_sid_denies_unavailable_principal_uniformly(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
    principal_state: str,
) -> None:
    """Registered signed SID cannot authenticate a missing/inactive/deleted user."""
    _uid, email, password = persisted_auth_user
    issued = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert issued.status_code == 200, issued.text
    access = issued.json()["access_token"]
    real_get = auth_deps.user_crud.get

    async def state_get(*args: object, **kwargs: object) -> User | None:
        existing = await real_get(*args, **kwargs)
        if principal_state == "missing":
            return None
        assert existing is not None
        if principal_state == "inactive":
            existing.active = False
        else:
            existing.deleted_at = datetime.now(tz=UTC)
        return existing

    monkeypatch.setattr(auth_deps.user_crud, "get", state_get)
    denied = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert denied.status_code == status.HTTP_401_UNAUTHORIZED, denied.text
    assert denied.json() == {"detail": "Token inválido o usuario no autorizado."}
    assert denied.headers.get("www-authenticate") == "Bearer"


async def test_registered_sid_database_lookup_outage_returns_503(
    api_client: httpx.AsyncClient,
    persisted_auth_user: tuple[uuid.UUID, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A session-ledger failure cannot be disguised as invalid credentials."""
    _uid, email, password = persisted_auth_user
    issued = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": email, "password": password},
    )
    assert issued.status_code == 200, issued.text

    async def ledger_unavailable(*_args: object, **_kwargs: object) -> bool:
        raise SQLAlchemyError("synthetic ledger outage")

    monkeypatch.setattr(auth_deps.session_ledger, "is_active", ledger_unavailable)
    denied = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {issued.json()['access_token']}"},
    )
    assert denied.status_code == status.HTTP_503_SERVICE_UNAVAILABLE, denied.text
    assert denied.json() == {"detail": "Persistencia de sesiones no disponible."}
    assert "synthetic ledger outage" not in denied.text

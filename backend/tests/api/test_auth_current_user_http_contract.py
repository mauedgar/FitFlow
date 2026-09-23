"""HTTP contract for access-token subject and current-user resolution."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta

import httpx
import pytest
from fastapi import status
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.core import security
from app.core.config import settings
from app.core.enums import UserRole
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
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Auth current-user HTTP contract requires fitflow_test; "
        f"configured database is {database_name!r}."
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
    monkeypatch: pytest.MonkeyPatch,
    persisted_auth_user: tuple[uuid.UUID, str, str],
) -> None:
    """Prove the real /auth/token -> returned access token -> /auth/me chain."""
    user_id, email, password = persisted_auth_user

    monkeypatch.setattr(
        auth_router,
        "store_refresh_token",
        lambda _user_id, _token: None,
    )

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
    assert response.json() == {"detail": "Token mal formado"}


async def test_me_with_valid_missing_user_id_preserves_404_contract(
    api_client: httpx.AsyncClient,
) -> None:
    """A valid UUID with no User row preserves bounded user-not-found behavior."""
    missing_user_id = uuid.uuid4()
    token = security.create_access_token(
        data={
            "sub": str(missing_user_id),
            "role": UserRole.client.value,
        }
    )

    response = await api_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Usuario no encontrado"}

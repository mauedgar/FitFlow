"""Issue108: strict signed refresh-owner binding on CI-only disposable Redis."""
from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from app.core import security
from app.core.config import settings
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key
from app.core.token_store import (
    REFRESH_PREFIX, delete_refresh_token, is_refresh_token_valid, store_refresh_token,
)
from app.core.redis_client import get_redis_client
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def strict_disposable_services() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"
    if os.getenv("GITHUB_ACTIONS") != "true":
        pytest.skip("Real Redis effects only on isolated GitHub Actions")
    url = urlparse(settings.REDIS_URL or "")
    assert (url.scheme, url.hostname, url.port, url.path) == (
        "redis", "127.0.0.1", 6379, "/0",
    )


@pytest.fixture(autouse=True)
async def dispose_test_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def subject() -> AsyncIterator[uuid.UUID]:
    identifier = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        db.add(User(
            id=identifier, email=f"registry-{identifier.hex}@example.com",
            hashed_password=security.get_password_hash("synthetic-only"),
            active=True,
        ))
        await db.commit()
    try:
        yield identifier
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id == identifier))
            await db.commit()


async def test_signed_registry_owner_and_opaque_positive_ttl(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    token = security.create_refresh_token({"sub": str(subject)})
    redis = get_redis_client()
    key = opaque_jwt_key(REFRESH_PREFIX, token)
    legacy = legacy_jwt_key(REFRESH_PREFIX, token)
    assert redis.exists(key) == 0 and redis.exists(legacy) == 0
    try:
        with pytest.raises(ValueError):
            store_refresh_token(str(uuid.uuid4()), token)
        store_refresh_token(str(subject), token)
        assert redis.get(key) == str(subject)
        assert redis.ttl(key) > 0
        assert redis.exists(legacy) == 0
        assert is_refresh_token_valid(token)
        answer = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": token},
        )
        assert answer.status_code == 200, answer.text
    finally:
        delete_refresh_token(token)


async def test_mismatched_redis_registry_rejects_refresh_and_logout(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    token = security.create_refresh_token({"sub": str(subject)})
    bearer = security.create_access_token({"sub": str(subject), "role": "client"})
    redis = get_redis_client()
    key = opaque_jwt_key(REFRESH_PREFIX, token)
    store_refresh_token(str(subject), token)
    try:
        redis.set(key, str(uuid.uuid4()), ex=120)
        assert not is_refresh_token_valid(token)
        response = await api_client.post(
            f"{settings.API_V1_STR}/auth/refresh", json={"refresh_token": token},
        )
        assert response.status_code == 401, response.text
        logout = await api_client.post(
            f"{settings.API_V1_STR}/auth/logout",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"refresh_token": token},
        )
        assert logout.status_code == 401, logout.text
    finally:
        delete_refresh_token(token)


async def test_legacy_registry_subject_mismatch_cannot_bypass_new_binding(
    subject: uuid.UUID,
) -> None:
    token = security.create_refresh_token({"sub": str(subject)})
    redis = get_redis_client()
    old = legacy_jwt_key(REFRESH_PREFIX, token)
    new = opaque_jwt_key(REFRESH_PREFIX, token)
    assert redis.exists(old) == 0 and redis.exists(new) == 0
    try:
        redis.set(old, str(uuid.uuid4()), ex=60)
        assert not is_refresh_token_valid(token)
        redis.set(old, str(subject), ex=60)
        assert is_refresh_token_valid(token)
        assert redis.exists(new) == 0
        redis.set(new, str(uuid.uuid4()), ex=60)
        assert not is_refresh_token_valid(token)  # No mismatched-opaque fallback.
    finally:
        redis.delete(old, new)


async def test_unregistered_signed_refresh_cannot_confirm_logout(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    token = security.create_refresh_token({"sub": str(subject)})
    bearer = security.create_access_token({"sub": str(subject), "role": "client"})
    assert not is_refresh_token_valid(token)
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Authorization": f"Bearer {bearer}"},
        json={"refresh_token": token},
    )
    assert response.status_code == 401, response.text


async def test_tampered_and_expired_signed_refresh_rejected_even_with_redis_key(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    """An existing Redis entry cannot override invalid signature or expiration."""
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    client = get_redis_client()
    valid = security.create_refresh_token({"sub": str(subject)})
    forged = valid.rsplit(".", 1)[0] + ".bad-signature"
    expired = jwt.encode(
        {
            "sub": str(subject),
            "token_use": "refresh",
            "exp": datetime.now(tz=UTC) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    keys = [
        opaque_jwt_key(REFRESH_PREFIX, forged),
        opaque_jwt_key(REFRESH_PREFIX, expired),
    ]
    assert all(client.exists(key) == 0 for key in keys)
    try:
        for token, key in zip((forged, expired), keys, strict=True):
            client.set(key, str(subject), ex=60)  # Stale or forged key attack.
            assert not is_refresh_token_valid(token)
            with pytest.raises(ValueError):
                store_refresh_token(str(subject), token)
            response = await api_client.post(
                f"{settings.API_V1_STR}/auth/refresh",
                json={"refresh_token": token},
            )
            assert response.status_code == 401, response.text
    finally:
        client.delete(*keys)


async def test_soft_deleted_account_denied_by_both_auth_pipelines(
    api_client: httpx.AsyncClient, subject: uuid.UUID,
) -> None:
    """Persisted account soft deletion overrides old, correctly signed bearer."""
    from datetime import UTC, datetime

    from sqlalchemy import update

    from app.services.auth_service import get_user_from_token
    from app.services.errors import AuthError

    signed = security.create_access_token({
        "sub": str(subject), "role": "front_desk",
    })
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User).where(User.id == subject).values(
                deleted_at=datetime.now(tz=UTC), active=True
            )
        )
        await db.commit()
        with pytest.raises(AuthError):
            await get_user_from_token(signed, db)
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/classes",
        headers={"Authorization": f"Bearer {signed}"},
    )
    assert response.status_code == 401, response.text

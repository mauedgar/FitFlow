"""Privacy contract: public paths never expose account identifiers anonymously.

Exercise real FastAPI auth, ORM and PostgreSQL 15 (disposable fitflow_test only).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import delete
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def isolated_pg_only() -> None:
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def dispose_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def account_ids() -> AsyncIterator[dict[str, UUID]]:
    ids = {role.value: uuid4() for role in UserRole}
    marker = uuid4().hex
    async with AsyncSessionLocal() as db:
        db.add_all([
            User(
                id=identity,
                email=f"privacy-{role}-{marker}@example.com",
                hashed_password="synthetic-test-only",
                role=UserRole(role),
                active=True,
            )
            for role, identity in ids.items()
        ])
        await db.commit()
    try:
        yield ids
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(User).where(User.id.in_(list(ids.values()))))
            await db.commit()


def bearer(ids: dict[str, UUID], role: str) -> dict[str, str]:
    token = create_access_token({"sub": str(ids[role]), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path_kind", ["directory", "detail"])
@pytest.mark.parametrize("authorization", ["missing", "malformed"])
async def test_unauthenticated_account_reads_never_return_personal_data(
    api_client: httpx.AsyncClient,
    account_ids: dict[str, UUID],
    path_kind: str,
    authorization: str,
) -> None:
    path = (
        "/users/public" if path_kind == "directory"
        else f"/users/{account_ids['client']}/public"
    )
    headers = {} if authorization == "missing" else {
        "Authorization": "Bearer invalid-not-a-token",
    }
    response = await api_client.get(f"{settings.API_V1_STR}{path}", headers=headers)
    assert response.status_code == 401, response.text
    assert response.headers.get("www-authenticate") == "Bearer"
    assert "privacy-" not in response.text


@pytest.mark.parametrize("role", ["client", "teacher", "front_desk"])
async def test_non_admin_cannot_enumerate_accounts(
    api_client: httpx.AsyncClient, account_ids: dict[str, UUID], role: str,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/users/public", headers=bearer(account_ids, role),
    )
    assert response.status_code == 403, response.text
    assert "privacy-" not in response.text


@pytest.mark.parametrize("role", ["client", "teacher", "front_desk"])
async def test_non_admin_can_read_only_own_account(
    api_client: httpx.AsyncClient, account_ids: dict[str, UUID], role: str,
) -> None:
    own = await api_client.get(
        f"{settings.API_V1_STR}/users/{account_ids[role]}/public",
        headers=bearer(account_ids, role),
    )
    assert own.status_code == 200, own.text
    assert own.json()["id"] == str(account_ids[role])
    assert own.json()["role"] == role
    assert own.json()["email"].startswith(f"privacy-{role}-")

    other = await api_client.get(
        f"{settings.API_V1_STR}/users/{account_ids['admin']}/public",
        headers=bearer(account_ids, role),
    )
    assert other.status_code == 403, other.text
    assert "privacy-" not in other.text


async def test_admin_can_read_directory_and_authorized_account(
    api_client: httpx.AsyncClient, account_ids: dict[str, UUID],
) -> None:
    headers = bearer(account_ids, "admin")
    response = await api_client.get(
        f"{settings.API_V1_STR}/users/public", headers=headers,
    )
    assert response.status_code == 200, response.text
    listed = {item["id"]: item for item in response.json()}
    # The existing CRUD directory is limited to the first 100 arbitrary rows;
    # this test must not assume newly created fixtures fall within that page.
    assert listed
    assert len(listed) <= 100
    for item in listed.values():
        assert set(item) == {"id", "email", "role", "active"}

    # Individual authorized lookup exercises every synthetic account without
    # enlarging or silently altering the existing directory pagination.
    for role, identity in account_ids.items():
        detail = await api_client.get(
            f"{settings.API_V1_STR}/users/{identity}/public", headers=headers,
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["id"] == str(identity)
        assert detail.json()["role"] == role


async def test_admin_nonexistent_account_returns_404_without_data(
    api_client: httpx.AsyncClient, account_ids: dict[str, UUID],
) -> None:
    missing = uuid4()
    response = await api_client.get(
        f"{settings.API_V1_STR}/users/{missing}/public",
        headers=bearer(account_ids, "admin"),
    )
    assert response.status_code == 404, response.text
    assert "privacy-" not in response.text

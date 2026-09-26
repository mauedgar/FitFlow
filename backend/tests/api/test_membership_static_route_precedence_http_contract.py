"""R008 HTTP contract for Membership static-route precedence."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import status

from app.core.deps import require_current_user
from app.core.enums import UserRole
from app.db.session import get_async_session
from app.main import app
from app.routers import memberships as memberships_router
from app.schemas.user import UserPublic

pytestmark = [pytest.mark.api, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
async def isolated_membership_dependencies() -> AsyncIterator[None]:
    async def override_db() -> AsyncIterator[object]:
        yield object()

    async def override_admin() -> UserPublic:
        return UserPublic(
            id=uuid.uuid4(),
            email="r008-admin@example.com",
            role=UserRole.admin,
            active=True,
        )

    app.dependency_overrides[get_async_session] = override_db
    app.dependency_overrides[require_current_user] = override_admin
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        app.dependency_overrides.pop(require_current_user, None)


@pytest.mark.parametrize(
    ("path", "expected_static_method"),
    [
        ("/api/v1/memberships/active", "get_multi_filtered"),
        ("/api/v1/memberships/stats", "get_multi"),
    ],
)
async def test_membership_static_routes_precede_dynamic_membership_id(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    expected_static_method: str,
) -> None:
    dynamic_get = AsyncMock(return_value=None)
    active_list = AsyncMock(return_value=[])
    stats_list = AsyncMock(return_value=[])

    monkeypatch.setattr(memberships_router.membership, "get", dynamic_get)
    monkeypatch.setattr(
        memberships_router.membership,
        "get_multi_filtered",
        active_list,
    )
    monkeypatch.setattr(memberships_router.membership, "get_multi", stats_list)

    response = await api_client.get(
        path,
        headers={"Authorization": "Bearer synthetic"},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == []
    assert dynamic_get.await_count == 0

    if expected_static_method == "get_multi_filtered":
        assert active_list.await_count == 1
        assert stats_list.await_count == 0
    else:
        assert active_list.await_count == 0
        assert stats_list.await_count == 1

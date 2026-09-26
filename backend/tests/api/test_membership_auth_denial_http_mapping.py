"""R009 Membership authenticated-denial HTTP mapping contract."""

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

MEMBERSHIP_ID = uuid.UUID("00000000-0000-4000-8000-000000000009")


@pytest.fixture(autouse=True)
async def isolated_membership_dependencies() -> AsyncIterator[None]:
    async def override_db() -> AsyncIterator[object]:
        yield object()

    app.dependency_overrides[get_async_session] = override_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        app.dependency_overrides.pop(require_current_user, None)


async def _request_for_role(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    role: UserRole | None,
) -> httpx.Response:
    monkeypatch.setattr(
        memberships_router.membership,
        "get_multi_filtered",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        memberships_router.membership,
        "get_multi",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        memberships_router.membership,
        "get",
        AsyncMock(return_value=None),
    )

    headers: dict[str, str] = {}
    if role is not None:
        async def override_current_user() -> UserPublic:
            return UserPublic(
                id=uuid.uuid4(),
                email=f"r009-{role.value}@example.com",
                role=role,
                active=True,
            )

        app.dependency_overrides[require_current_user] = override_current_user
        headers["Authorization"] = "Bearer synthetic"

    return await api_client.get(path, headers=headers)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/memberships/active",
        "/api/v1/memberships/stats",
        f"/api/v1/memberships/{MEMBERSHIP_ID}",
    ],
)
async def test_membership_selected_routes_require_authentication(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    response = await _request_for_role(api_client, monkeypatch, path, None)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        ("/api/v1/memberships/active", status.HTTP_200_OK),
        ("/api/v1/memberships/stats", status.HTTP_200_OK),
        (f"/api/v1/memberships/{MEMBERSHIP_ID}", status.HTTP_404_NOT_FOUND),
    ],
)
async def test_membership_selected_routes_allow_admin_boundary(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    expected_status: int,
) -> None:
    response = await _request_for_role(
        api_client,
        monkeypatch,
        path,
        UserRole.admin,
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/memberships/active",
        "/api/v1/memberships/stats",
        f"/api/v1/memberships/{MEMBERSHIP_ID}",
    ],
)
async def test_membership_selected_routes_reject_teacher_with_403(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    response = await _request_for_role(
        api_client,
        monkeypatch,
        path,
        UserRole.teacher,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert response.json() == {
        "detail": "Este recurso requiere uno de los siguientes roles: admin."
    }
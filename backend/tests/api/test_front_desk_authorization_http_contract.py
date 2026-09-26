"""R007 HTTP authorization contract for the Front Desk classes route."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from app.core.deps import require_current_user
from app.core.enums import UserRole
from app.db.session import get_async_session
from app.main import app
from app.routers import front_desk as front_desk_router
from app.schemas.user import UserPublic
from fastapi import status

pytestmark = [pytest.mark.api, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
async def isolated_front_desk_dependencies() -> AsyncIterator[None]:
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
    role: UserRole | None,
) -> httpx.Response:
    async def fake_get_active_classes(_db: object) -> list[object]:
        return []

    monkeypatch.setattr(
        front_desk_router.front_desk_service,
        "get_active_classes",
        fake_get_active_classes,
    )

    headers: dict[str, str] = {}
    if role is not None:
        async def override_current_user() -> UserPublic:
            return UserPublic(
                id=uuid.uuid4(),
                email=f"r007-{role.value}@example.com",
                role=role,
                active=True,
            )

        app.dependency_overrides[require_current_user] = override_current_user
        headers["Authorization"] = "Bearer synthetic"

    return await api_client.get(
        "/api/v1/front-desk/classes",
        headers=headers,
    )


@pytest.mark.parametrize("role", [UserRole.admin, UserRole.front_desk])
async def test_front_desk_classes_allows_authorized_roles(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    role: UserRole,
) -> None:
    response = await _request_for_role(api_client, monkeypatch, role)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == []


@pytest.mark.parametrize("role", [UserRole.teacher, UserRole.client])
async def test_front_desk_classes_rejects_disallowed_roles_with_403(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    role: UserRole,
) -> None:
    response = await _request_for_role(api_client, monkeypatch, role)

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.text
    assert response.json() == {
        "detail": (
            "Este recurso requiere uno de los siguientes roles: "
            "admin, front_desk."
        )
    }


async def test_front_desk_classes_requires_authentication(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = await _request_for_role(api_client, monkeypatch, None)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers.get("www-authenticate") == "Bearer"

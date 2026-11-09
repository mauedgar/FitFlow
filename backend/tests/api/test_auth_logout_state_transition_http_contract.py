"""HTTP contract for logout token-state transition behavior."""

from __future__ import annotations

import uuid
import httpx
import pytest
from app.core import security
from app.core.config import settings
from app.routers import auth as auth_router
from fastapi import status

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture
def authenticated_owner(monkeypatch: pytest.MonkeyPatch) -> uuid.UUID:
    # Existing negative transition tests are bounded, synthetic Redis stubs.
    # They test transition ordering, not actual redis registration.
    monkeypatch.setattr(auth_router, "is_refresh_token_valid", lambda _token: True)
    monkeypatch.setattr(auth_router, "is_token_blacklisted", lambda _token: False)
    return uuid.uuid4()

def _refresh_token(user_id: uuid.UUID) -> str:
    return security.create_refresh_token(data={"sub": str(user_id)})


async def _post_logout(
    api_client: httpx.AsyncClient,
    refresh_token: str,
    *,
    access_token: str | None = None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    return await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": refresh_token},
        headers=headers,
    )


async def test_logout_rejects_unregistered_signed_refresh_without_access(
    api_client: httpx.AsyncClient,
) -> None:
    refresh_token = _refresh_token(uuid.uuid4())
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh token no registrado o revocado."}

async def test_logout_owner_deletes_refresh_then_blacklists(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(authenticated_owner)
    events: list[tuple[str, str]] = []

    def delete_refresh(token: str) -> None:
        events.append(("delete", token))

    def blacklist(token: str) -> None:
        events.append(("blacklist", token))

    monkeypatch.setattr(auth_router, "delete_refresh_token", delete_refresh)
    monkeypatch.setattr(auth_router, "blacklist_token", blacklist)
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.request.url.query == b""
    assert response.content == b""
    assert events == [
        ("delete", refresh_token),
        ("blacklist", refresh_token),
    ]

async def test_logout_malformed_refresh_token_returns_400_without_state_change(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        auth_router,
        "delete_refresh_token",
        lambda _token: events.append("delete"),
    )
    monkeypatch.setattr(
        auth_router,
        "blacklist_token",
        lambda _token: events.append("blacklist"),
    )
    response = await _post_logout(api_client, "definitely-not-a-jwt")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.request.url.query == b""
    assert "definitely-not-a-jwt" not in response.text
    assert response.json() == {"detail": "Refresh token inválido."}
    assert events == []

async def test_logout_cross_user_refresh_token_returns_403_without_state_change(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(uuid.uuid4())
    signed_access = security.create_access_token(
        {"sub": str(authenticated_owner), "role": "client"},
    )
    events: list[str] = []
    monkeypatch.setattr(
        auth_router,
        "delete_refresh_token",
        lambda _token: events.append("delete"),
    )
    monkeypatch.setattr(
        auth_router,
        "blacklist_token",
        lambda _token: events.append("blacklist"),
    )
    response = await _post_logout(
        api_client, refresh_token, access_token=signed_access,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "La sesión no coincide con el token de refresco."}
    assert events == []

async def test_logout_delete_external_service_error_maps_503_before_blacklist(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(authenticated_owner)
    events: list[str] = []

    def unavailable_delete(_token: str) -> None:
        events.append("delete")
        raise auth_router.ExternalServiceError("Redis no está disponible.")

    def blacklist(_token: str) -> None:
        events.append("blacklist")

    monkeypatch.setattr(auth_router, "delete_refresh_token", unavailable_delete)
    monkeypatch.setattr(auth_router, "blacklist_token", blacklist)
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está disponible."}
    assert events == ["delete"]

async def test_logout_blacklist_external_service_error_maps_503_after_delete(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(authenticated_owner)
    events: list[str] = []

    def delete_refresh(_token: str) -> None:
        events.append("delete")

    def unavailable_blacklist(_token: str) -> None:
        events.append("blacklist")
        raise auth_router.ExternalServiceError("Redis no está disponible.")

    monkeypatch.setattr(auth_router, "delete_refresh_token", delete_refresh)
    monkeypatch.setattr(auth_router, "blacklist_token", unavailable_blacklist)
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está disponible."}
    assert events == ["delete", "blacklist"]

async def test_logout_delete_generic_failure_maps_500_before_blacklist(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(authenticated_owner)
    events: list[str] = []

    def failing_delete(_token: str) -> None:
        events.append("delete")
        raise RuntimeError("synthetic delete failure")

    def blacklist(_token: str) -> None:
        events.append("blacklist")

    monkeypatch.setattr(auth_router, "delete_refresh_token", failing_delete)
    monkeypatch.setattr(auth_router, "blacklist_token", blacklist)
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}
    assert events == ["delete"]

async def test_logout_blacklist_generic_failure_maps_500_after_delete(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    authenticated_owner: uuid.UUID,
) -> None:
    refresh_token = _refresh_token(authenticated_owner)
    events: list[str] = []

    def delete_refresh(_token: str) -> None:
        events.append("delete")

    def failing_blacklist(_token: str) -> None:
        events.append("blacklist")
        raise RuntimeError("synthetic blacklist failure")

    monkeypatch.setattr(auth_router, "delete_refresh_token", delete_refresh)
    monkeypatch.setattr(auth_router, "blacklist_token", failing_blacklist)
    response = await _post_logout(api_client, refresh_token)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}
    assert events == ["delete", "blacklist"]

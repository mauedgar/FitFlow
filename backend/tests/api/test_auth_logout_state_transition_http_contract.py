"""HTTP negative contracts for atomic refresh/session logout.

The real Redis script is covered separately by the disposable PG15/Redis7
integration suite. These stubs assert HTTP boundary, not Redis atomicity.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from fastapi import status

from app.core import security
from app.core.config import settings
from app.routers import auth as auth_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


def _refresh_token(user_id: uuid.UUID) -> str:
    return security.create_refresh_token(data={"sub": str(user_id)})


async def _post_logout(
    api_client: httpx.AsyncClient,
    refresh_token: str,
    *, access_token: str | None = None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    return await api_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": refresh_token},
        headers=headers,
    )


async def test_logout_rejects_unregistered_signed_refresh_without_access(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth_router, "commit_logout", lambda *_args, **_kwargs: False)
    response = await _post_logout(api_client, _refresh_token(uuid.uuid4()))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Refresh token no registrado o revocado."}


async def test_logout_owner_confirms_single_commit_without_token_in_response(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = uuid.uuid4()
    refresh = _refresh_token(subject)
    events: list[tuple[str, str | None]] = []

    def confirm(token: str, *, sid: str | None, access_token: str | None, subject: str) -> bool:
        events.append((token, sid))
        assert access_token is None
        assert subject == str(owner)
        return True

    owner = subject
    monkeypatch.setattr(auth_router, "commit_logout", confirm)
    response = await _post_logout(api_client, refresh)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.request.url.query == b""
    assert response.content == b""
    assert events == [(refresh, None)]


async def test_logout_malformed_refresh_token_returns_400_without_state_change(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(auth_router, "commit_logout", lambda *_args, **_kwargs: events.append("write"))
    response = await _post_logout(api_client, "definitely-not-a-jwt")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Refresh token inválido."}
    assert "definitely-not-a-jwt" not in response.text
    assert events == []


async def test_logout_cross_user_refresh_token_returns_403_without_state_change(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    refresh = _refresh_token(uuid.uuid4())
    access = security.create_access_token({"sub": str(uuid.uuid4()), "role": "client"})
    monkeypatch.setattr(auth_router, "commit_logout", lambda *_args, **_kwargs: events.append("write"))
    response = await _post_logout(api_client, refresh, access_token=access)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "La sesión no coincide con el token de refresco."}
    assert events == []


async def test_logout_redis_failure_before_ack_maps_503(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> bool:
        raise auth_router.ExternalServiceError("Redis no está disponible.")

    monkeypatch.setattr(auth_router, "commit_logout", unavailable)
    response = await _post_logout(api_client, _refresh_token(uuid.uuid4()))
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Redis no está disponible."}


async def test_logout_unknown_redis_result_never_reports_success(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unconfirmed(*_args: object, **_kwargs: object) -> bool:
        raise auth_router.ExternalServiceError("Resultado de revocación Redis no confirmado.")

    monkeypatch.setattr(auth_router, "commit_logout", unconfirmed)
    response = await _post_logout(api_client, _refresh_token(uuid.uuid4()))
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


async def test_logout_generic_commit_failure_maps_500(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failure(*_args: object, **_kwargs: object) -> bool:
        raise RuntimeError("synthetic atomic commit failure")

    monkeypatch.setattr(auth_router, "commit_logout", failure)
    response = await _post_logout(api_client, _refresh_token(uuid.uuid4()))
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error interno"}


async def test_logout_previous_confirmed_commit_returns_204(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Duplicate acknowledgement is safe only when verified by Redis; the
    # integration suite checks that the confirmation marker exists.
    monkeypatch.setattr(auth_router, "commit_logout", lambda *_args, **_kwargs: True)
    response = await _post_logout(api_client, _refresh_token(uuid.uuid4()))
    assert response.status_code == status.HTTP_204_NO_CONTENT

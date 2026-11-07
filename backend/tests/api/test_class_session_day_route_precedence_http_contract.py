"""HTTP regression for static class-session day route precedence (#96).

This runs against the registered FastAPI app; no database or real users are used.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import status

from app.db.session import get_async_session
from app.main import app
from app.routers import class_sessions as class_sessions_router

pytestmark = [pytest.mark.api, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
async def isolate_class_session_http_dependencies() -> AsyncIterator[None]:
    """Do not open PostgreSQL connections for route ordering tests."""
    async def override_db() -> AsyncIterator[object]:
        yield object()

    prior = app.dependency_overrides.get(get_async_session)
    app.dependency_overrides[get_async_session] = override_db
    try:
        yield
    finally:
        if prior is None:
            app.dependency_overrides.pop(get_async_session, None)
        else:
            app.dependency_overrides[get_async_session] = prior


@pytest.mark.parametrize("requested_day", ["2026-11-07", "2026-02-28"])
async def test_day_route_wins_over_dynamic_uuid(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    requested_day: str,
) -> None:
    """A date must reach the day handler, never the session UUID handler."""
    filtered = AsyncMock(return_value=[])
    by_id = AsyncMock(return_value=None)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)

    response = await api_client.get(
        "/api/v1/class-sessions/day",
        params={"date_query": requested_day},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == []
    filtered.assert_awaited_once()
    kwargs = filtered.await_args.kwargs
    assert kwargs["include_relations"] is True
    assert kwargs["date_from"].date() == date.fromisoformat(requested_day)
    assert kwargs["date_to"].date() == date.fromisoformat(requested_day)
    assert kwargs["date_from"] <= kwargs["date_to"]
    by_id.assert_not_awaited()


async def test_invalid_day_is_validation_error_without_db_query(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filtered = AsyncMock(return_value=[])
    by_id = AsyncMock(return_value=None)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)

    response = await api_client.get(
        "/api/v1/class-sessions/day",
        params={"date_query": "not-a-date"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    filtered.assert_not_awaited()
    by_id.assert_not_awaited()


async def test_uuid_session_route_remains_accessible(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = uuid.uuid4()
    by_id = AsyncMock(return_value=None)
    filtered = AsyncMock(return_value=[])
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)

    response = await api_client.get(f"/api/v1/class-sessions/{session_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    by_id.assert_awaited_once()
    assert by_id.await_args.kwargs["obj_id"] == session_id
    filtered.assert_not_awaited()

"""HTTP contract for static class-session route precedence (#96).

Use a fresh FastAPI app per test. No DB, global app dependency override, or
real user is touched. A negative control recreates the baseline route ordering.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, status

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import get_async_session
from app.main import app as production_app
from app.routers import class_sessions as class_sessions_router

pytestmark = [pytest.mark.api, pytest.mark.asyncio]
PREFIX = f"{settings.API_V1_STR}/class-sessions"


@pytest.fixture
async def isolated_api_client() -> AsyncIterator[httpx.AsyncClient]:
    """Clone registered v1 router to avoid mutating main app overrides."""
    application = FastAPI()
    application.include_router(api_router, prefix=settings.API_V1_STR)

    async def override_db() -> AsyncIterator[object]:
        yield object()

    application.dependency_overrides[get_async_session] = override_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application, raise_app_exceptions=False),
        base_url="http://fitflow.test",
    ) as client:
        yield client


def _route_index(application: FastAPI, suffix: str) -> int:
    """Compare the already mounted path suffix, independent of mutable settings."""
    indices = [
        index for index, route in enumerate(application.router.routes)
        if str(getattr(route, "path", "")).endswith(suffix)
        and "GET" in (getattr(route, "methods", None) or set())
    ]
    assert indices, f"missing production GET route ending {suffix}"
    return indices[0]


async def test_production_registration_places_day_before_uuid_handler() -> None:
    """The actual app route table must obey the same static-before-dynamic order."""
    assert _route_index(production_app, "/class-sessions/day") < _route_index(
        production_app, "/class-sessions/{session_id}"
    )


async def test_negative_control_reproduces_legacy_order_422() -> None:
    """A minimal FastAPI app proves why the previous registration order fails."""
    legacy_app = FastAPI()

    @legacy_app.get("/class-sessions/{session_id}")
    async def legacy_uuid(session_id: uuid.UUID) -> dict[str, str]:
        return {"id": str(session_id)}

    @legacy_app.get("/class-sessions/day")
    async def legacy_day(date_query: date) -> list[str]:
        return [date_query.isoformat()]

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=legacy_app, raise_app_exceptions=False),
        base_url="http://fitflow.test",
    ) as client:
        response = await client.get(
            "/class-sessions/day", params={"date_query": "2026-11-07"}
        )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("requested_day", ["2026-11-07", "2026-02-28"])
async def test_day_route_wins_over_dynamic_uuid(
    isolated_api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    requested_day: str,
) -> None:
    filtered = AsyncMock(return_value=[])
    by_id = AsyncMock(return_value=None)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)

    response = await isolated_api_client.get(
        f"{PREFIX}/day", params={"date_query": requested_day}
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


async def test_invalid_day_does_not_query_database(
    isolated_api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filtered = AsyncMock(return_value=[])
    by_id = AsyncMock(return_value=None)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)

    response = await isolated_api_client.get(
        f"{PREFIX}/day", params={"date_query": "not-a-date"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    filtered.assert_not_awaited()
    by_id.assert_not_awaited()


async def test_uuid_session_route_remains_accessible(
    isolated_api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = uuid.uuid4()
    by_id = AsyncMock(return_value=None)
    filtered = AsyncMock(return_value=[])
    monkeypatch.setattr(class_sessions_router.class_session, "get", by_id)
    monkeypatch.setattr(class_sessions_router.class_session, "get_multi_filtered", filtered)

    response = await isolated_api_client.get(f"{PREFIX}/{session_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text
    by_id.assert_awaited_once()
    assert by_id.await_args.kwargs["obj_id"] == session_id
    filtered.assert_not_awaited()

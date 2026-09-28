"""HTTP contract for liveness and dependency readiness."""

import logging

import httpx
import pytest

from app.core import readiness

pytestmark = [pytest.mark.api, pytest.mark.asyncio]


async def test_liveness_reports_process_availability(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


async def test_readiness_reports_healthy_dependencies(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def all_dependencies_ready() -> list[str]:
        return []

    monkeypatch.setattr(readiness, "get_unavailable_dependencies", all_dependencies_ready)

    response = await api_client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_readiness_fails_closed_and_logs_without_exposing_dependency(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def redis_unavailable() -> list[str]:
        return ["redis"]

    monkeypatch.setattr(readiness, "get_unavailable_dependencies", redis_unavailable)

    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = await api_client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "redis" not in response.text
    assert "Readiness check failed for: redis" in caplog.text

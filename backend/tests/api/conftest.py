"""Shared HTTP fixtures scoped to FitFlow API tests."""

from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import app


@pytest.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    """Yield an in-process async client against the real FastAPI application."""
    transport = httpx.ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://fitflow.test",
    ) as client:
        yield client
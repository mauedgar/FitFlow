"""A12 boundary: client IP comes from trusted ASGI scope, not HTTP claims.

This is a hermetic negative HTTP test, NOT a staging proxy configuration PASS.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest
from app.core.config import settings
from app.db.session import engine
from app.routers import auth as auth_router
from pydantic import ValidationError
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
async def dispose_test_engine_pool() -> AsyncIterator[None]:
    """Isolate asyncpg connections from subsequent pytest event loops."""
    yield
    await engine.dispose()


async def test_ir012_spoofed_forwarding_headers_cannot_choose_throttle_origin(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"
    captured: list[tuple[str, str]] = []

    def capture(username: str, remote: str) -> None:
        captured.append((username, remote))

    monkeypatch.setattr(auth_router, "check_login_throttle", capture)
    identity = f"ir012-missing-{uuid4().hex}@example.com"
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": identity, "password": "synthetic-invalid-only"},
        headers={
            "X-Forwarded-For": "198.51.100.33",
            "X-Real-IP": "203.0.113.42",
            "Forwarded": "for=192.0.2.7;proto=https",
        },
    )
    assert response.status_code == 401, response.text
    assert captured == [(identity, "127.0.0.1")]
    assert all(spoof not in str(captured) for spoof in (
        "198.51.100.33", "203.0.113.42", "192.0.2.7",
    ))


async def test_ir012_staging_cannot_disable_login_limiter_with_testing_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import Settings

    # Only a settings object is instantiated; no staging services are started.
    common = {
        "_env_file": None,
        "ENV": "staging",
        "DATABASE_URL": "postgresql://fitflow:secret@postgres:5432/fitflow",
        "BACKEND_CORS_ORIGINS": ["https://staging.fitflow.example"],
        "DEBUG": False,
        "TESTING": True,
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "SECRET_KEY": "isolated-test-only-012",
    }
    with pytest.raises(ValidationError, match="TESTING must be false"):
        Settings(**common)  # type: ignore[arg-type]

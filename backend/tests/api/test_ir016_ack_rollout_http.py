"""A10 staged mandatory-ACK compatibility gate (synthetic no real account)."""
from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
from app.core.config import settings
from app.routers import auth as auth_router
from pydantic import ValidationError

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


async def test_required_staging_ack_rejects_headerless_before_db_or_redis(
    api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def unexpected(**kwargs: object) -> None:
        calls.append("called")

    monkeypatch.setattr(settings, "REFRESH_ACK_POLICY", "required")
    monkeypatch.setattr(auth_router, "check_login_throttle", unexpected)
    account = f"synthetic-ir016-{uuid4().hex}@example.invalid"
    response = await api_client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": account, "password": "synthetic-only"},
    )
    assert response.status_code == 426
    assert calls == []


async def test_compatibility_policy_is_explicit_and_validated() -> None:
    from app.core.config import Settings
    with pytest.raises(ValidationError, match="REFRESH_ACK_POLICY"):
        Settings(_env_file=None, DATABASE_URL="postgresql://a:b@localhost/db",
                 SECRET_KEY="unit-test-only", REFRESH_ACK_POLICY="wildcard")


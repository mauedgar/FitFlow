"""Synthetic Redis throttle contract with no production addresses or credentials."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.config import settings
from app.core.login_throttle import LIMIT, WINDOW_SECONDS, check_login_throttle, login_rate_key
from app.core.redis_client import get_redis_client
from fastapi import HTTPException

pytestmark = [pytest.mark.api, pytest.mark.integration]


def test_atomic_login_throttle_limits_attempts_without_leaking_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert settings.TESTING is True
    assert settings.REDIS_URL == "redis://127.0.0.1:6379/0"
    username = f"throttle-{uuid4().hex}@example.invalid"
    host = "192.0.2.201"
    key = login_rate_key(username, host)
    assert username not in key and host not in key
    client = get_redis_client()
    try:
        assert client.exists(key) == 0
        monkeypatch.setattr(settings, "TESTING", False)
        for _ in range(LIMIT):
            check_login_throttle(username, host)
        with pytest.raises(HTTPException) as error:
            check_login_throttle(username, host)
        assert error.value.status_code == 429
        assert error.value.headers == {"Retry-After": str(WINDOW_SECONDS)}
        assert 0 < client.ttl(key) <= WINDOW_SECONDS
    finally:
        client.delete(key)
        client.close()


def test_throttle_does_not_bypass_real_redis_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert settings.TESTING is True
    monkeypatch.setattr(settings, "TESTING", False)
    monkeypatch.setattr(settings, "REDIS_URL", None)
    with pytest.raises(Exception, match="Redis no está configurado"):
        check_login_throttle("missing@example.invalid", "192.0.2.202")

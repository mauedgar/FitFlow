"""Registration must reject unhashable new passwords before any DB write."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import settings
from app.routers import users as user_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37, "test\x00password"])
async def test_register_invalid_bcrypt_password_returns_422_without_crud(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    password: str,
) -> None:
    async def unexpected_lookup(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("invalid password must not reach user lookup")

    monkeypatch.setattr(user_router.user_crud, "get_by_email", unexpected_lookup)
    response = await api_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": "issue43@example.com", "password": password},
    )
    assert response.status_code == 422, response.text

"""Registration must reject unhashable new passwords before any DB write."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.main import app
from app.routers import users as user_router
from app.schemas.user import UserCreate

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.mark.parametrize("password", ["a" * 73, "ñ" * 37, "ñ" * 36 + "a", "a" * 71 + "ñ", "test\x00password"])
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


@pytest.mark.parametrize("password", ["a" * 72, "ñ" * 36, "a" * 70 + "ñ"])
async def test_register_valid_exact_72_byte_password_reaches_create_without_mutation(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    password: str,
) -> None:
    """Positive HTTP 201 contract uses synthetic CRUD doubles, not the database."""
    assert len(password.encode("utf-8")) == 72
    calls: list[str] = []
    synthetic_id = uuid4()

    async def fake_lookup(*, db: object, email: str, include_deleted: bool) -> None:
        del db
        assert email == "issue43@example.com"
        assert include_deleted
        calls.append("lookup")

    async def fake_create(*, db: object, obj_in: UserCreate) -> SimpleNamespace:
        del db
        assert obj_in.password == password
        calls.append("create")
        return SimpleNamespace(
            id=synthetic_id,
            email=obj_in.email,
            role=UserRole.client,
            active=True,
        )

    monkeypatch.setattr(user_router.user_crud, "get_by_email", fake_lookup)
    monkeypatch.setattr(user_router.user_crud, "create", fake_create)
    response = await api_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": "issue43@example.com", "password": password},
    )

    assert response.status_code == 201, response.text
    assert response.json()["id"] == str(synthetic_id)
    assert calls == ["lookup", "create"]


async def test_user_password_update_http_route_is_not_exposed() -> None:
    """UserUpdate is internal CRUD/schema only; do not invent an HTTP 422 update route."""
    # Match the actual mounted routes, independently of mutable test settings.
    # Positive registration HTTP tests above still enforce the configured prefix.
    user_routes = [
        route
        for route in app.routes
        if "/users" in getattr(route, "path", "")
    ]
    assert any(
        getattr(route, "path", "").endswith("/users/register")
        for route in user_routes
    ), "users registration router must actually be mounted"
    assert all(
        not ({"PUT", "PATCH"} & set(getattr(route, "methods", set())))
        for route in user_routes
    )

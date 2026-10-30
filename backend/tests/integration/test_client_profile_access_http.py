"""HTTP routing and account/profile authorization regressions for /clients.

Uses the actual FastAPI route/dependency graph, isolated fake CRUD and no
persistent DB or secrets. SQL-level access is validated separately in CI.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.deps import require_current_user
from app.core.enums import UserRole
from app.crud.crud_client import client as crud_client
from app.db.session import get_async_session
from app.routers.clients import router
from app.schemas.user import UserPublic


@pytest.fixture
def http_clients(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    account_id = uuid4()
    profile_id = uuid4()
    subject = {"id": account_id, "role": UserRole.client}
    profile = SimpleNamespace(
        id=profile_id,
        user_id=account_id,
        first_name="Ana",
        last_name="Gómez",
        document_number=None,
        address=None,
        medical_fit_url=None,
        profile_image_url=None,
        created_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
        user=SimpleNamespace(email="ana@example.com"),
        bookings=[],
        membership=None,
    )

    def current_user():
        return UserPublic(
            id=subject["id"], role=subject["role"],
            email="ana@example.com", active=True,
        )

    app.dependency_overrides[require_current_user] = current_user
    app.dependency_overrides[get_async_session] = lambda: object()

    async def get_by_user_id(*, db, user_id, include_relations=False):
        return profile if user_id == account_id else None

    async def get(*, db, obj_id):
        return profile if obj_id == profile_id else None

    async def get_with_relations(*, db, client_id):
        return profile if client_id == profile_id else None

    async def get_multi(*, db, skip, limit, options):
        return [profile]

    async def update(*, db, db_obj, obj_in):
        return db_obj

    monkeypatch.setattr(crud_client, "get_by_user_id", get_by_user_id)
    monkeypatch.setattr(crud_client, "get", get)
    monkeypatch.setattr(crud_client, "get_with_relations", get_with_relations)
    monkeypatch.setattr(crud_client, "get_multi", get_multi)
    monkeypatch.setattr(crud_client, "update", update)
    with TestClient(app) as http:
        yield http, subject, profile


@pytest.mark.parametrize("path", [
    "/clients/me",
    "/clients/me/bookings",
    "/clients/me/membership",
    "/clients/me/stats",
    "/clients/me/activity",
])
def test_own_profile_static_paths_are_reachable_by_client(http_clients, path):
    http, _, profile = http_clients
    result = http.get(path)
    assert result.status_code == 200, result.text
    assert result.json()["id"] == str(profile.id)


@pytest.mark.parametrize("path", [
    "/clients/me",
    "/clients/me/bookings",
    "/clients/me/membership",
    "/clients/me/stats",
    "/clients/me/activity",
])
@pytest.mark.parametrize("role", [UserRole.teacher, UserRole.front_desk, UserRole.admin])
def test_own_profile_static_paths_deny_non_client_roles(http_clients, path, role):
    http, subject, _ = http_clients
    subject["role"] = role
    assert http.get(path).status_code == 403


def test_admin_listing_denies_client_and_allows_admin(http_clients):
    http, subject, _ = http_clients
    assert http.get("/clients/").status_code == 403
    subject["role"] = UserRole.admin
    result = http.get("/clients/")
    assert result.status_code == 200, result.text
    assert result.json()[0]["full_name"] == "Ana Gómez"


def test_client_id_access_uses_profile_user_id_not_profile_id(http_clients):
    http, subject, profile = http_clients
    assert subject["id"] != profile.id
    result = http.get(f"/clients/{profile.id}")
    assert result.status_code == 200, result.text
    subject["id"] = uuid4()
    assert http.get(f"/clients/{profile.id}").status_code == 403


def test_client_cannot_update_another_account_profile(http_clients):
    http, subject, profile = http_clients
    subject["id"] = uuid4()
    assert http.put(f"/clients/{profile.id}", json={"first_name": "Otro"}).status_code == 403


def test_admin_can_read_profile_by_id(http_clients):
    http, subject, profile = http_clients
    subject["role"] = UserRole.admin
    result = http.get(f"/clients/{profile.id}")
    assert result.status_code == 200, result.text


@pytest.mark.asyncio
async def test_user_profile_lookup_filters_soft_deleted(monkeypatch):
    from app.crud.crud_client import client

    observed = {}

    class FakeSession:
        async def execute(self, statement):
            observed["sql"] = str(statement.compile())
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(first=lambda: None)
            )

    assert await client.get_by_user_id(
        db=FakeSession(), user_id=uuid4()
    ) is None
    assert "deleted_at IS NULL" in observed["sql"]

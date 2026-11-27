"""Security P0: real HTTP auth boundaries with only disposable test DB fixtures.

Exercise routing, signed JWT guards and mutations, not direct handler calls.
Never point these tests at retained staging or production data.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
from types import SimpleNamespace
from sqlalchemy.engine import make_url
import auth_session_test_helpers as fixture_guard

import httpx
import pytest
from jose import jwt
from fastapi import status
from sqlalchemy import func, select

from app.core.config import settings
from app.core.enums import ActivityType, UserRole
from auth_session_test_helpers import (
    capture_http_creations, cleanup_synthetic_fixture, committed_access, finish_synthetic_cleanup,
    require_local_test_database, require_local_test_redis,
    require_postgres15_test_service, staged_access,
)
from app.core.security import create_access_token, decode_token
from app.db.models import Client, GymClass, Teacher, User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]
API = settings.API_V1_STR


@dataclass(frozen=True)
class SecurityActors:
    marker: str
    class_id: uuid.UUID
    class_name: str
    admin_user_id: uuid.UUID
    tokens: dict[str, str]

    def headers(self, role: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens[role]}"}


@pytest.fixture(autouse=True)
def require_disposable_database() -> None:
    require_local_test_database()


@pytest.fixture(autouse=True)
async def dispose_async_pool_between_tests() -> AsyncIterator[None]:
    """Never reuse an asyncpg connection bound to another pytest event loop."""
    yield
    await engine.dispose()


@pytest.fixture
async def actors() -> AsyncIterator[SecurityActors]:
    marker = uuid.uuid4().hex
    class_name = f"P0 Audit {marker}"
    users = [
        User(
            id=uuid.uuid4(),
            email=f"p0-{marker}-{role.value}@example.com",
            hashed_password="synthetic-no-login",
            role=role,
        )
        for role in (UserRole.admin, UserRole.client, UserRole.teacher, UserRole.front_desk)
    ]
    inactive = User(
        id=uuid.uuid4(),
        email=f"p0-{marker}-inactive@example.com",
        hashed_password="synthetic-no-login",
        role=UserRole.client,
        active=False,
    )
    gym_class = GymClass(
        id=uuid.uuid4(),
        name=class_name,
        description="Disposable security route fixture",
        activity_type=ActivityType.group_class,
        duration_minutes=60,
        default_capacity=8,
    )
    owned_user_ids = tuple(user.id for user in [*users, inactive])
    try:
        async with AsyncSessionLocal() as db:
            db.add_all([*users, inactive, gym_class])
            await db.commit()
        identities = {user.role.value: user.id for user in users}
        tokens = {
            name: await committed_access(user_id, name)
            for name, user_id in identities.items()
        }
        tokens["inactive"] = await committed_access(inactive.id, "client")
        tokens["forged_admin"] = await committed_access(identities["client"], "admin")
        yield SecurityActors(
            marker=marker,
            class_id=gym_class.id,
            class_name=class_name,
            admin_user_id=identities["admin"],
            tokens=tokens,
        )
    finally:
        await finish_synthetic_cleanup(cleanup_synthetic_fixture(
            user_ids=owned_user_ids,
            gym_class_ids=(gym_class.id,),
        ))


@pytest.mark.parametrize("supplied_role", ["admin", "teacher", "front_desk", "client"])
async def test_public_registration_rejects_any_role_and_creates_no_user(
    api_client: httpx.AsyncClient,
    supplied_role: str,
) -> None:
    email = f"p0-spoof-{uuid.uuid4().hex}@example.com"
    async with capture_http_creations(email=email):
        response = await api_client.post(
            f"{API}/users/register",
            json={
                "email": email,
                "password": "Synthetic-password-not-a-secret",
                "role": supplied_role,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
        async with AsyncSessionLocal() as db:
            assert await db.scalar(select(User).where(User.email == email)) is None


async def test_public_registration_remains_client_only_and_accepts_legacy_full_name(
    api_client: httpx.AsyncClient,
) -> None:
    email = f"p0-new-{uuid.uuid4().hex}@example.com"
    async with capture_http_creations(email=email):
        response = await api_client.post(
            f"{API}/users/register",
            json={
                "email": email,
                "password": "Synthetic-password-not-a-secret",
                "full_name": "Synthetic User",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED, response.text
        assert response.json()["role"] == "client"
        assert response.json()["email"] == email
        async with AsyncSessionLocal() as db:
            stored = await db.scalar(select(User).where(User.email == email))
            assert stored is not None
            assert stored.role == UserRole.client


@pytest.mark.parametrize("path_kind", ["list", "detail"])
@pytest.mark.parametrize("actor", ["guest", "client", "teacher", "front_desk"])
async def test_user_identity_endpoints_deny_public_and_non_admin(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    path_kind: str,
    actor: str,
) -> None:
    path = (
        f"{API}/users/public"
        if path_kind == "list"
        else f"{API}/users/{actors.admin_user_id}/public"
    )
    response = await api_client.get(
        path,
        headers={} if actor == "guest" else actors.headers(actor),
    )
    expected = (
        status.HTTP_401_UNAUTHORIZED
        if actor == "guest"
        else status.HTTP_403_FORBIDDEN
    )
    assert response.status_code == expected, response.text
    assert "p0-" not in response.text


@pytest.mark.parametrize("path_kind", ["list", "detail"])
async def test_user_identity_endpoints_allow_admin(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    path_kind: str,
) -> None:
    path = (
        f"{API}/users/public"
        if path_kind == "list"
        else f"{API}/users/{actors.admin_user_id}/public"
    )
    response = await api_client.get(path, headers=actors.headers("admin"))
    assert response.status_code == status.HTTP_200_OK, response.text
    payload = response.json()
    if path_kind == "list":
        # The directory may be paginated and contain >100 pre-existing fixtures.
        assert isinstance(payload, list)
        assert all({"id", "email", "role", "active"} <= item.keys() for item in payload)
    else:
        assert payload["id"] == str(actors.admin_user_id)


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
@pytest.mark.parametrize("actor", ["guest", "client", "teacher", "front_desk"])
async def test_class_mutators_deny_unauthorized_without_side_effects(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
    method: str,
    actor: str,
) -> None:
    path = (
        f"{API}/gym-classes/"
        if method == "POST"
        else f"{API}/gym-classes/{actors.class_id}"
    )
    payload = (
        {
            "name": f"P0 Audit {actors.marker} unauthorized",
            "description": "Must not persist",
            "duration_minutes": 60,
            "default_capacity": 8,
            "activity_type": "group_class",
        }
        if method == "POST"
        else {"name": f"P0 Audit {actors.marker} overwritten"}
        if method == "PUT"
        else None
    )
    marker_name = payload["name"] if method == "POST" else None
    async with capture_http_creations(class_name=marker_name):
        response = await api_client.request(
            method,
            path,
            headers={} if actor == "guest" else actors.headers(actor),
            json=payload,
        )
        expected = status.HTTP_401_UNAUTHORIZED if actor == "guest" else status.HTTP_403_FORBIDDEN
        assert response.status_code == expected, response.text
        async with AsyncSessionLocal() as db:
            original = await db.scalar(select(GymClass).where(GymClass.id == actors.class_id))
            assert original is not None and original.name == actors.class_name
            count = await db.scalar(
                select(func.count()).select_from(GymClass).where(
                    GymClass.name.like(f"P0 Audit {actors.marker}%")
                )
            )
            assert count == 1


async def test_admin_can_create_update_and_soft_delete_class(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    headers = actors.headers("admin")
    name = f"P0 Audit {actors.marker} admin-created"
    async with capture_http_creations(class_name=name):
        created = await api_client.post(
            f"{API}/gym-classes/",
            headers=headers,
            json={
                "name": name,
                "description": "Admin-only controlled creation",
                "duration_minutes": 60,
                "default_capacity": 8,
                "activity_type": "group_class",
            },
        )
        assert created.status_code == status.HTTP_201_CREATED, created.text
        new_id = created.json()["id"]
        edited = await api_client.put(
            f"{API}/gym-classes/{new_id}",
            headers=headers,
            json={"name": name + " updated"},
        )
        assert edited.status_code == status.HTTP_200_OK, edited.text
        assert edited.json()["name"] == name + " updated"
        removed = await api_client.delete(
            f"{API}/gym-classes/{new_id}",
            headers=headers,
        )
        assert removed.status_code == status.HTTP_202_ACCEPTED, removed.text


async def test_public_class_catalog_stays_accessible_without_credentials(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(f"{API}/gym-classes/public")
    assert response.status_code == status.HTTP_200_OK, response.text
    assert any(item["id"] == str(actors.class_id) for item in response.json())


async def test_identity_directory_rejects_invalid_and_expired_jwt(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    invalid = await api_client.get(
        f"{API}/users/public",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED
    expired = create_access_token(
        {"sub": str(actors.admin_user_id), "role": "admin"},
        expires_delta=timedelta(seconds=-1),
    )
    expired_response = await api_client.get(
        f"{API}/users/public",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert expired_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_admin_claim_in_jwt_cannot_override_persisted_client_role(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(
        f"{API}/users/public",
        headers=actors.headers("forged_admin"),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "p0-" not in response.text


async def test_inactive_user_is_denied_even_with_signed_token(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    response = await api_client.get(
        f"{API}/users/public",
        headers=actors.headers("inactive"),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("www-authenticate") == "Bearer"
    assert response.json() == {"detail": "Token inválido o usuario no autorizado."}
    assert "p0-" not in response.text


async def test_auth_me_preserves_valid_admin_identity_and_rejects_invalid_token(
    api_client: httpx.AsyncClient,
    actors: SecurityActors,
) -> None:
    valid = await api_client.get(
        f"{API}/auth/me",
        headers=actors.headers("admin"),
    )
    assert valid.status_code == status.HTTP_200_OK, valid.text
    assert valid.json()["id"] == str(actors.admin_user_id)
    invalid = await api_client.get(
        f"{API}/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert invalid.status_code == status.HTTP_401_UNAUTHORIZED



@pytest.mark.parametrize(
    "invalid_url",
    [
        "postgresql://synthetic@remote.example/fitflow_test",
        "postgresql://synthetic@127.0.0.1/fitflow_prod",
        "postgresql://synthetic@127.0.0.1:5555/fitflow_test",
        "postgresql://synthetic@127.0.0.1/fitflow_test?host=remote.example.org",
        "postgresql://synthetic@127.0.0.1/fitflow_test?sslmode=prefer",
    ],
)
async def test_synthetic_session_helper_denies_non_disposable_database_even_without_assert(
    monkeypatch: pytest.MonkeyPatch, invalid_url: str,
) -> None:
    """A RuntimeError—not an optimized-away assert—must precede DB writes."""
    monkeypatch.setattr(settings, "DATABASE_URL", invalid_url)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        require_local_test_database()


@pytest.mark.parametrize(
    ("env", "testing"),
    [("production", True), ("test", False), ("development", True)],
)
async def test_synthetic_session_helper_denies_non_test_profiles_before_db_access(
    monkeypatch: pytest.MonkeyPatch, env: str, testing: bool,
) -> None:
    """Check settings directly; no remote connection is made by these tests."""
    monkeypatch.setattr(settings, "ENV", env)
    monkeypatch.setattr(settings, "TESTING", testing)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        require_local_test_database()


@pytest.mark.parametrize(
    "engine_override",
    [
        {"drivername": "sqlite+aiosqlite"},
        {"host": "remote.example.org"},
        {"database": "fitflow_retained"},
        {"port": 5555},
    ],
)
async def test_synthetic_preflight_rejects_actual_engine_mismatch_without_io(
    monkeypatch: pytest.MonkeyPatch, engine_override: dict[str, object],
) -> None:
    expected = make_url(settings.DATABASE_URL_ASYNC)
    fake = SimpleNamespace(url=expected.set(**engine_override), dialect=engine.dialect)
    monkeypatch.setattr(fixture_guard, "engine", fake)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        fixture_guard.require_local_test_database()


async def test_synthetic_preflight_rejects_non_postgres_actual_dialect_without_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = SimpleNamespace(
        url=make_url(settings.DATABASE_URL_ASYNC),
        dialect=SimpleNamespace(name="sqlite", driver="aiosqlite"),
    )
    monkeypatch.setattr(fixture_guard, "engine", fake)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        fixture_guard.require_local_test_database()


@pytest.mark.parametrize(
    "redis_url",
    [
        None, "redis://remote.example.org:6379/0",
        "redis://127.0.0.1:6380/0", "redis://127.0.0.1:6379/1",
        "redis://guest@127.0.0.1:6379/0",
        "redis://127.0.0.1:6379/0?unsafe=true",
    ],
)
async def test_synthetic_redis_preflight_rejects_unsafe_target_without_io(
    monkeypatch: pytest.MonkeyPatch, redis_url: str | None,
) -> None:
    monkeypatch.setattr(settings, "REDIS_URL", redis_url)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        require_local_test_redis()


async def test_cleanup_joins_original_despite_repeated_caller_cancellation() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    finished = asyncio.Event()

    async def cleanup() -> None:
        started.set()
        await release.wait()
        finished.set()

    owner = asyncio.create_task(finish_synthetic_cleanup(cleanup()))
    try:
        await started.wait()
        owner.cancel()
        await asyncio.sleep(0)
        owner.cancel()
        await asyncio.sleep(0)
        assert not owner.done()
    finally:
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await owner
    assert finished.is_set()


async def test_cleanup_timeout_quarantines_and_joins_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(fixture_guard, "_CLEANUP_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(fixture_guard, "_cleanup_quarantined", False)
    finished = asyncio.Event()

    async def slow_cleanup() -> None:
        await asyncio.sleep(0.03)
        finished.set()

    with pytest.raises(pytest.exit.Exception, match="original joined"):
        await finish_synthetic_cleanup(slow_cleanup())
    assert finished.is_set()
    with pytest.raises(RuntimeError, match="quarantined"):
        fixture_guard.require_local_test_database()


async def test_actual_engine_query_override_rejected_without_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = SimpleNamespace(
        url=make_url(settings.DATABASE_URL_ASYNC).update_query_dict({"host": "remote.example.org"}),
        dialect=engine.dialect,
    )
    monkeypatch.setattr(fixture_guard, "engine", fake)
    with pytest.raises(RuntimeError, match="BLOCKED_PRECONDITION"):
        fixture_guard.require_local_test_database()


@dataclass(frozen=True)
class ProfileActors:
    user_ids: dict[str, uuid.UUID]
    profile_ids: dict[str, uuid.UUID]
    tokens: dict[str, str]

    def headers(self, name: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens[name]}"}


@pytest.fixture
async def profile_actors() -> AsyncIterator[ProfileActors]:
    """Capture actual inserted user identities; all profiles belong to them."""
    await require_postgres15_test_service()
    marker = uuid.uuid4().hex
    accounts = {
        name: User(
            id=uuid.uuid4(), email=f"profile-{marker}-{name}@example.com",
            hashed_password="synthetic-no-login", role=role, active=True,
        )
        for name, role in (
            ("teacher", UserRole.teacher), ("peer", UserRole.teacher),
            ("client", UserRole.client), ("admin", UserRole.admin),
        )
    }
    profiles = {
        name: model(
            id=uuid.uuid4(), user_id=accounts[name].id,
            first_name=f"Synthetic {name}", last_name=marker,
        )
        for name, model in (("teacher", Teacher), ("peer", Teacher), ("client", Client))
    }
    async with capture_http_creations(email=accounts["teacher"].email):
        async with AsyncSessionLocal() as db:
            db.add_all(list(accounts.values()))
            await db.flush()
            db.add_all(list(profiles.values()))
            tokens = {
                name: staged_access(db, account.id, account.role.value)
                for name, account in accounts.items()
            }
            await db.commit()
        yield ProfileActors(
            user_ids={name: account.id for name, account in accounts.items()},
            profile_ids={name: profile.id for name, profile in profiles.items()},
            tokens=tokens,
        )


async def test_self_profile_and_stats_resolve_authenticated_account(
    api_client: httpx.AsyncClient, profile_actors: ProfileActors,
) -> None:
    for name in ("teacher", "peer", "client", "admin"):
        # An unrelated query identifier must never become the resource selector.
        query = {"user_id": str(profile_actors.user_ids["admin"])}
        response = await api_client.get(
            f"{API}/users/me", params=query, headers=profile_actors.headers(name),
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == str(profile_actors.user_ids[name])
        if name in ("teacher", "peer"):
            assert data["teacher"]["id"] == str(profile_actors.profile_ids[name])
            assert data["client"] is None
        elif name == "client":
            assert data["client"]["id"] == str(profile_actors.profile_ids[name])
            assert data["teacher"] is None
        else:
            assert data["client"] is None and data["teacher"] is None
        stats = await api_client.get(
            f"{API}/users/me/stats", params=query, headers=profile_actors.headers(name),
        )
        assert stats.status_code == 200, stats.text
        assert stats.json()["id"] == str(profile_actors.user_ids[name])
        assert stats.json()["total_bookings"] == 0
        assert stats.json()["upcoming_bookings"] == 0
        assert stats.json()["total_classes_taught"] == 0


async def test_teacher_private_get_put_bind_persisted_profile_owner(
    api_client: httpx.AsyncClient, profile_actors: ProfileActors,
) -> None:
    own_id = profile_actors.profile_ids["teacher"]
    other_id = profile_actors.profile_ids["peer"]
    assert own_id != profile_actors.user_ids["teacher"]
    own = f"{API}/teachers/{own_id}"
    other = f"{API}/teachers/{other_id}"
    response = await api_client.get(own, headers=profile_actors.headers("teacher"))
    assert response.status_code == 200, response.text
    assert response.json()["id"] == str(own_id)
    for actor in ("peer", "client"):
        denied = await api_client.get(own, headers=profile_actors.headers(actor))
        assert denied.status_code == 403, denied.text
        denied = await api_client.put(
            own, headers=profile_actors.headers(actor), json={"bio": "must not write"},
        )
        assert denied.status_code == 403, denied.text
    denied = await api_client.put(
        other, headers=profile_actors.headers("teacher"),
        params={"teacher_id": str(own_id)}, json={"bio": "must not write"},
    )
    assert denied.status_code == 403, denied.text
    updated = await api_client.put(
        own, headers=profile_actors.headers("teacher"), json={"bio": "owned update"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["bio"] == "owned update"
    peer = await api_client.get(other, headers=profile_actors.headers("admin"))
    assert peer.status_code == 200, peer.text
    assert peer.json()["id"] == str(other_id) and peer.json()["bio"] is None
    admin_update = await api_client.put(
        other, headers=profile_actors.headers("admin"), json={"bio": "admin update"},
    )
    assert admin_update.status_code == 200, admin_update.text
    assert admin_update.json()["bio"] == "admin update"


async def test_fractional_access_expiration_denied_by_both_bearer_pipelines(
    api_client: httpx.AsyncClient, actors: SecurityActors,
) -> None:
    payload = decode_token(actors.tokens["admin"])
    assert payload is not None
    payload["exp"] = int(datetime.now(tz=UTC).timestamp()) + 90.5
    malformed = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    for path in (f"{API}/auth/me", f"{API}/teachers/"):
        response = await api_client.get(path, headers={"Authorization": f"Bearer {malformed}"})
        assert response.status_code == 401, response.text
        assert response.headers.get("WWW-Authenticate") == "Bearer"

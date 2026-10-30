"""Real database HTTP authorization contract for client profiles.

Uses the existing isolated fitflow_test PostgreSQL schema, actual JWT guards,
SQLAlchemy ORM mappings, and real FastAPI ASGI routing. No external credentials.
"""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError

import httpx
import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import (
    ActivityType, BookingStatus, ClassSessionStatus, MembershipPlan,
    MembershipStatus, UserRole,
)
from app.core.security import create_access_token
from app.db.models import (
    Booking, ClassSchedule, ClassSession, Client, GymClass, Membership, User,
)
from app.db.session import AsyncSessionLocal, engine
from app.crud.crud_client import client as crud_client
from app.crud.crud_user import user as crud_user
from app.routers import users as users_router

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@dataclass(frozen=True)
class ClientProfileFixture:
    owner_id: uuid.UUID
    profile_id: uuid.UUID
    neighbor_id: uuid.UUID
    deleted_id: uuid.UUID
    owner_email: str
    membership_id: uuid.UUID
    booking_id: uuid.UUID
    unprofiled_user_id: uuid.UUID
    deleted_user_profile_id: uuid.UUID
    tokens: dict[str, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        f"Client profile HTTP contract requires fitflow_test; got {database_name!r}"
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def profile_fixture() -> ClientProfileFixture:
    marker = uuid.uuid4().hex
    owner_email = f"client-profile-owner-{marker}@example.com"
    owner = Client(
        first_name="Ana",
        last_name="Cliente",
        user=User(
            email=owner_email,
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    neighbor = Client(
        first_name="Otra",
        last_name="Persona",
        user=User(
            email=f"client-profile-neighbor-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    deleted = Client(
        first_name="Baja",
        last_name="Logica",
        deleted_at=datetime.now(timezone.utc),
        user=User(
            email=f"client-profile-deleted-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    admin = User(
        email=f"client-profile-admin-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.admin,
    )
    teacher = User(
        email=f"client-profile-teacher-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.teacher,
    )
    unprofiled = User(
        email=f"client-profile-new-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    deleted_user_client = Client(
        first_name="Account",
        last_name="Deleted",
        user=User(
            email=f"client-profile-user-deleted-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
            deleted_at=datetime.now(timezone.utc),
        ),
    )
    start = datetime.now(timezone.utc) + timedelta(days=2)
    membership = Membership(
        client=owner,
        plan=MembershipPlan.premium,
        status=MembershipStatus.active,
        start_date=datetime.now(timezone.utc) - timedelta(days=3),
        end_date=datetime.now(timezone.utc) + timedelta(days=40),
    )
    gym_class = GymClass(
        name=f"Client Profile Class {marker}",
        description="Profile HTTP contract class",
        activity_type=ActivityType.open_gym,
        duration_minutes=60,
        default_capacity=10,
    )
    schedule = ClassSchedule(
        gym_class=gym_class,
        teacher=None,
        rrule="RRULE:FREQ=DAILY;COUNT=1",
        start_date=date.today(),
        start_time=time(10, 0),
        duration_minutes=60,
        capacity=10,
    )
    session = ClassSession(
        class_schedule=schedule,
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        capacity_snapshot=10,
        status=ClassSessionStatus.scheduled,
    )
    booking = Booking(client=owner, class_session=session, status=BookingStatus.confirmed)

    async with AsyncSessionLocal() as db:
        db.add_all([
            owner, neighbor, deleted, admin, teacher, unprofiled,
            deleted_user_client, membership, gym_class, schedule, session, booking,
        ])
        await db.flush()
        owner_id = owner.user_id
        profile_id = owner.id
        neighbor_id = neighbor.id
        deleted_id = deleted.id
        membership_id = membership.id
        booking_id = booking.id
        unprofiled_user_id = unprofiled.id
        deleted_user_profile_id = deleted_user_client.id
        actors = {
            "owner": owner.user_id,
            "neighbor": neighbor.user_id,
            "deleted": deleted.user_id,
            "admin": admin.id,
            "teacher": teacher.id,
            "deleted_user": deleted_user_client.user_id,
        }
        await db.commit()

    tokens = {
        name: create_access_token({"sub": str(identity), "role": (
            UserRole.admin.value if name == "admin"
            else UserRole.teacher.value if name == "teacher"
            else UserRole.client.value
        )})
        for name, identity in actors.items()
    }
    return ClientProfileFixture(
        owner_id=owner_id,
        profile_id=profile_id,
        neighbor_id=neighbor_id,
        deleted_id=deleted_id,
        owner_email=owner_email,
        membership_id=membership_id,
        booking_id=booking_id,
        unprofiled_user_id=unprofiled_user_id,
        deleted_user_profile_id=deleted_user_profile_id,
        tokens=tokens,
    )


def headers(fixture: ClientProfileFixture, name: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[name]}"}


async def test_admin_list_real_orm_projection_and_soft_delete(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        params={"skip": 0, "limit": 1000},
        headers=headers(profile_fixture, "admin"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    items = {item["id"]: item for item in result.json()}
    profile = items[str(profile_fixture.profile_id)]
    assert profile["full_name"] == "Ana Cliente"
    assert profile["email"] == profile_fixture.owner_email
    assert profile["phone"] is None
    assert profile["created_at"]
    assert str(profile_fixture.deleted_id) not in items


@pytest.mark.parametrize("name", ["owner", "teacher"])
async def test_admin_list_rejects_unauthorized_roles(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        headers=headers(profile_fixture, name),
    )
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_client_me_real_jwt_and_orm(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, "owner"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    assert result.json()["id"] == str(profile_fixture.profile_id)
    assert result.json()["email"] == profile_fixture.owner_email


@pytest.mark.parametrize("name", ["admin", "teacher"])
async def test_client_me_rejects_other_roles(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, name),
    )
    assert result.status_code == status.HTTP_403_FORBIDDEN


async def test_soft_deleted_profile_not_accessible_through_me(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/clients/me",
        headers=headers(profile_fixture, "deleted"),
    )
    assert result.status_code == status.HTTP_404_NOT_FOUND


async def test_client_cannot_read_or_update_neighbors_profile(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    base = f"{settings.API_V1_STR}/clients/{profile_fixture.neighbor_id}"
    get_result = await api_client.get(base, headers=headers(profile_fixture, "owner"))
    put_result = await api_client.put(
        base,
        json={"first_name": "No"},
        headers=headers(profile_fixture, "owner"),
    )
    assert get_result.status_code == status.HTTP_403_FORBIDDEN
    assert put_result.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("path", [
    "/clients/me/bookings", "/clients/me/membership",
    "/clients/me/stats", "/clients/me/activity",
])
async def test_own_profile_with_real_membership_and_booking_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    path: str,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}{path}",
        headers=headers(profile_fixture, "owner"),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    body = response.json()
    assert body["id"] == str(profile_fixture.profile_id)
    if path.endswith("/membership"):
        assert body["membership"]["id"] == str(profile_fixture.membership_id)
        assert body["membership"]["is_active"] is True
        assert body["membership"]["is_expired"] is False
    if path.endswith("/bookings"):
        assert len(body["bookings"]) == 1
        assert body["bookings"][0]["id"] == str(profile_fixture.booking_id)
        assert body["bookings"][0]["gym_class_name"].startswith("Client Profile Class")
    if path.endswith("/stats"):
        assert body["total_bookings"] == 1
        assert len(body["upcoming_bookings"]) == 1
    if path.endswith("/activity"):
        assert len(body["upcoming_bookings"]) == 1


@pytest.mark.parametrize("name", ["owner", "admin"])
async def test_get_and_put_private_client_profile_with_real_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    name: str,
) -> None:
    url = f"{settings.API_V1_STR}/clients/{profile_fixture.profile_id}"
    get_result = await api_client.get(url, headers=headers(profile_fixture, name))
    assert get_result.status_code == status.HTTP_200_OK, get_result.text
    body = get_result.json()
    assert len(body["bookings"]) == 1
    assert body["bookings"][0]["gym_class_name"].startswith("Client Profile Class")
    assert body["membership"]["is_active"] is True

    put_result = await api_client.put(
        url, json={"first_name": "Renamed"},
        headers=headers(profile_fixture, name),
    )
    assert put_result.status_code == status.HTTP_200_OK, put_result.text
    assert put_result.json()["first_name"] == "Renamed"
    assert len(put_result.json()["bookings"]) == 1
    assert put_result.json()["membership"]["id"] == str(profile_fixture.membership_id)


async def test_admin_create_client_serializes_empty_real_relations(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    response = await api_client.post(
        f"{settings.API_V1_STR}/clients/{profile_fixture.unprofiled_user_id}",
        json={"first_name": "New", "last_name": "Profile"},
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    assert response.json()["first_name"] == "New"
    assert response.json()["bookings"] == []
    assert response.json()["membership"] is None


async def test_membership_client_projection_has_preloaded_user(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    result = await api_client.get(
        f"{settings.API_V1_STR}/memberships/{profile_fixture.membership_id}",
        headers=headers(profile_fixture, "admin"),
    )
    assert result.status_code == status.HTTP_200_OK, result.text
    assert result.json()["client"]["email"] == profile_fixture.owner_email


@pytest.mark.parametrize("credential", ["absent", "invalid", "expired", "missing_user", "deleted_user"])
async def test_client_profile_authentication_failures_are_http_401(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    credential: str,
) -> None:
    if credential == "absent":
        request_headers = {}
    elif credential == "invalid":
        request_headers = {"Authorization": "Bearer this-is-not-a-jwt"}
    elif credential == "expired":
        request_headers = {"Authorization": "Bearer " + create_access_token(
            {"sub": str(profile_fixture.owner_id), "role": UserRole.client.value},
            expires_delta=timedelta(seconds=-1),
        )}
    elif credential == "deleted_user":
        request_headers = headers(profile_fixture, "deleted_user")
    else:
        request_headers = {"Authorization": "Bearer " + create_access_token(
            {"sub": str(uuid.uuid4()), "role": UserRole.client.value}
        )}
    response = await api_client.get(
        f"{settings.API_V1_STR}/clients/me", headers=request_headers,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    assert response.headers.get("www-authenticate") == "Bearer"


async def test_admin_list_ignores_soft_deleted_users(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        params={"limit": 1000},
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    ids = {item["id"] for item in response.json()}
    assert str(profile_fixture.deleted_user_profile_id) not in ids


async def test_admin_put_deleted_account_profile_has_no_write_effect(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    target_id = profile_fixture.deleted_user_profile_id
    result = await api_client.put(
        f"{settings.API_V1_STR}/clients/{target_id}",
        json={"first_name": "MustNotPersist"},
        headers=headers(profile_fixture, "admin"),
    )
    assert result.status_code == status.HTTP_404_NOT_FOUND
    async with AsyncSessionLocal() as db:
        saved = await db.scalar(select(Client).where(Client.id == target_id))
        assert saved is not None
        assert saved.first_name == "Account"


async def test_registration_denies_duplicate_email_of_soft_deleted_user(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    async with AsyncSessionLocal() as db:
        deleted_user_id = await db.scalar(
            select(Client.user_id).where(
                Client.id == profile_fixture.deleted_user_profile_id
            )
        )
        assert deleted_user_id is not None
        deleted = await db.scalar(select(User).where(User.id == deleted_user_id))
        assert deleted is not None
        deleted_email = deleted.email

    response = await api_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={"email": deleted_email, "password": "SafeContractOnly-42"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    assert response.json() == {"detail": "El email ya está registrado."}


@pytest.mark.parametrize("params", [
    {"skip": -1}, {"limit": 0}, {"limit": -1}, {"limit": 1001},
])
async def test_admin_list_rejects_invalid_page_bounds(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    params: dict[str, int],
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/clients/",
        params=params,
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


async def test_locked_client_detail_blocks_concurrent_account_soft_delete(
    profile_fixture: ClientProfileFixture,
) -> None:
    """A separate session cannot soft-delete User while Client PUT owns its lock."""
    async with AsyncSessionLocal() as owner_db, AsyncSessionLocal() as other_db:
        target = await crud_client.get_with_relations(
            db=owner_db,
            client_id=profile_fixture.profile_id,
            for_update=True,
        )
        assert target is not None
        await other_db.execute(text("SET LOCAL lock_timeout = '250ms'"))
        with pytest.raises(DBAPIError) as failure:
            await other_db.execute(
                update(User)
                .where(User.id == profile_fixture.owner_id)
                .values(deleted_at=datetime.now(timezone.utc))
            )
        assert getattr(failure.value.orig, "sqlstate", None) == "55P03"
        await other_db.rollback()
        await owner_db.rollback()


async def test_registration_unique_collision_after_precheck_is_http_400(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate two registrars passing precheck; exercise PostgreSQL UNIQUE."""
    async def skipped_precheck(*, db, email, include_relations=False, include_deleted=False):
        return None

    monkeypatch.setattr(crud_user, "get_by_email", skipped_precheck)
    result = await api_client.post(
        f"{settings.API_V1_STR}/users/register",
        json={
            "email": profile_fixture.owner_email,
            "password": "SafeContractOnly-42",
        },
    )
    assert result.status_code == status.HTTP_400_BAD_REQUEST, result.text
    assert result.json() == {"detail": "El email ya está registrado."}
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(User).where(User.email == profile_fixture.owner_email)
        )
        assert existing is not None


async def test_membership_stats_live_booking_relations_are_preloaded(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
) -> None:
    """Existing Membership with a real Booking must render without lazy raises."""
    response = await api_client.get(
        f"{settings.API_V1_STR}/memberships/stats",
        headers=headers(profile_fixture, "admin"),
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    actual = next(
        (item for item in response.json() if item["id"] == str(profile_fixture.membership_id)),
        None,
    )
    assert actual is not None
    assert actual["total_bookings"] == 1
    assert str(profile_fixture.booking_id) in actual["upcoming_bookings"]


@pytest.mark.parametrize("constraint_name, expected", [
    ("ix_users_email", True),
    ("uq_users_other_unique", False),
    (None, False),
])
async def test_email_unique_error_classifier_only_matches_email_index(
    constraint_name: str | None, expected: bool,
) -> None:
    class PGUniqueException(Exception):
        sqlstate = "23505"

        def __init__(self, name: str | None):
            super().__init__(f'duplicate key value violates unique constraint "{name}"')
            self.constraint_name = name

    error = __import__("sqlalchemy").exc.IntegrityError(
        "INSERT INTO users", {}, PGUniqueException(constraint_name),
    )
    assert users_router._is_email_unique_violation(error) is expected


async def test_email_unique_error_classifier_rejects_non_unique_sqlstate() -> None:
    class PGForeignKeyException(Exception):
        sqlstate = "23503"
        constraint_name = "ix_users_email"

    error = __import__("sqlalchemy").exc.IntegrityError(
        "INSERT INTO users", {}, PGForeignKeyException(),
    )
    assert not users_router._is_email_unique_violation(error)


async def test_concurrent_http_put_then_delete_serializes_client_profile(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUT holds row locks; an actual concurrent HTTP DELETE follows its commit."""
    from app.crud.crud_client import client as crud_client_local

    locked = asyncio.Event()
    continue_put = asyncio.Event()
    delete_started = asyncio.Event()
    original_detail = crud_client_local.get_with_relations
    original_get = crud_client_local.get

    async def paused_detail(*, db, client_id, for_update=False):
        result = await original_detail(db=db, client_id=client_id, for_update=for_update)
        if for_update:
            locked.set()
            await asyncio.wait_for(continue_put.wait(), timeout=10)
        return result

    async def observed_delete_get(*, db, obj_id, **kwargs):
        result = await original_get(db=db, obj_id=obj_id, **kwargs)
        if obj_id == profile_fixture.profile_id:
            delete_started.set()
        return result

    monkeypatch.setattr(crud_client_local, "get_with_relations", paused_detail)
    monkeypatch.setattr(crud_client_local, "get", observed_delete_get)
    url = f"{settings.API_V1_STR}/clients/{profile_fixture.profile_id}"
    admin_headers = headers(profile_fixture, "admin")
    put_task = asyncio.create_task(api_client.put(
        url, json={"first_name": "BeforeDelete"}, headers=admin_headers
    ))
    delete_task = None
    try:
        await asyncio.wait_for(locked.wait(), timeout=10)
        delete_task = asyncio.create_task(api_client.delete(url, headers=admin_headers))
        await asyncio.wait_for(delete_started.wait(), timeout=10)
        assert not put_task.done()
        assert not delete_task.done()
    finally:
        continue_put.set()
    response_put = await asyncio.wait_for(put_task, timeout=15)
    assert response_put.status_code == status.HTTP_200_OK, response_put.text
    assert delete_task is not None
    response_delete = await asyncio.wait_for(delete_task, timeout=15)
    assert response_delete.status_code == status.HTTP_202_ACCEPTED, response_delete.text
    async with AsyncSessionLocal() as db:
        saved = await db.scalar(
            select(Client).where(Client.id == profile_fixture.profile_id)
        )
        assert saved is not None
        assert saved.first_name == "BeforeDelete"
        assert saved.deleted_at is not None


async def test_concurrent_http_delete_then_put_never_writes_deleted_profile(
    api_client: httpx.AsyncClient,
    profile_fixture: ClientProfileFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deletion acquires row lock first; concurrent PUT must observe 404 afterward."""
    from app.crud.crud_client import client as crud_client_local

    deleting = asyncio.Event()
    allow_delete_commit = asyncio.Event()
    original_remove = crud_client_local.remove

    async def paused_remove(*, db, db_obj, hard=False):
        # Lock the real database row; leave the actual soft-delete to CRUDBase.
        assert not hard
        await db.execute(
            select(Client.id)
            .where(Client.id == db_obj.id)
            .with_for_update(of=Client)
        )
        deleting.set()
        await asyncio.wait_for(allow_delete_commit.wait(), timeout=15)
        return await original_remove(db=db, db_obj=db_obj, hard=hard)

    async def assert_put_is_waiting_on_delete_lock():
        # Observe PostgreSQL's lock manager, not just an HTTP task or timer.
        query = text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid <> pg_backend_pid()
                  AND wait_event_type = 'Lock'
                  AND cardinality(pg_blocking_pids(pid)) > 0
                  AND query ILIKE '%FOR UPDATE%'
                  AND query ILIKE '%clients%'
            )
            """
        )
        async with AsyncSessionLocal() as observer:
            for _ in range(100):
                if await observer.scalar(query):
                    return
                await observer.rollback()
                await asyncio.sleep(0.05)
        pytest.fail("PUT never reached a PostgreSQL FOR UPDATE lock wait")

    monkeypatch.setattr(crud_client_local, "remove", paused_remove)
    url = f"{settings.API_V1_STR}/clients/{profile_fixture.profile_id}"
    admin_headers = headers(profile_fixture, "admin")
    delete_task = asyncio.create_task(api_client.delete(url, headers=admin_headers))
    put_task = None
    try:
        await asyncio.wait_for(deleting.wait(), timeout=15)
        put_task = asyncio.create_task(
            api_client.put(
                url, json={"first_name": "MustNotPersist"}, headers=admin_headers
            )
        )
        await asyncio.wait_for(assert_put_is_waiting_on_delete_lock(), timeout=12)
        assert not put_task.done(), "PUT must still be waiting on DELETE's row lock"
        assert not delete_task.done(), "DELETE must still hold its row lock"
    finally:
        allow_delete_commit.set()
    delete_response = await asyncio.wait_for(delete_task, timeout=15)
    assert delete_response.status_code == status.HTTP_202_ACCEPTED, delete_response.text
    assert put_task is not None
    put_response = await asyncio.wait_for(put_task, timeout=15)
    assert put_response.status_code == status.HTTP_404_NOT_FOUND, put_response.text
    async with AsyncSessionLocal() as db:
        saved = await db.scalar(
            select(Client).where(Client.id == profile_fixture.profile_id)
        )
        assert saved is not None
        assert saved.deleted_at is not None
        assert saved.first_name == "Ana"

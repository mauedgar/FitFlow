"""Exact PostgreSQL SID registration for isolated functional HTTP test credentials.

Never bypass Product authentication. Fixture callers must COMMIT their
current PostgreSQL transaction before using these signed access JWTs.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Sequence
from contextlib import asynccontextmanager
from contextvars import ContextVar
from urllib.parse import urlparse
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, event, or_, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.crud.auth_session import fingerprint, signed_refresh_family
from app.db.models import (
    Booking,
    ClassSchedule,
    ClassSession,
    Client,
    GymClass,
    Membership,
    Person,
    Teacher,
    User,
)
from app.db.models.auth_session import AuthSession
from app.db.session import AsyncSessionLocal, engine


_CLEANUP_TIMEOUT_SECONDS = 15.0
_cleanup_quarantined = False
_creation_scope: ContextVar[object | None] = ContextVar("synthetic_http_creation_scope", default=None)


def require_local_test_database() -> None:
    """Fail before any synthetic INSERT, even if no bearer will be minted."""
    if _cleanup_quarantined:
        raise RuntimeError("BLOCKED_PRECONDITION: test process quarantined after unresolved cleanup")
    target = make_url(settings.DATABASE_URL)
    actual = engine.url  # The connection pool was constructed before tests.
    if not (
        target.drivername in {"postgresql", "postgresql+asyncpg"}
        and target.database == "fitflow_test"
        and (target.host or "").lower() in {"127.0.0.1", "localhost", "::1"}
        and target.port in {None, 5432, 55432}
        and not target.query  # No asyncpg query option can override the destination.
        and not actual.query
        and actual == target.set(drivername="postgresql+asyncpg")
        and engine.dialect.name == "postgresql"
        and engine.dialect.driver == "asyncpg"
        and settings.ENV == "test"
        and settings.TESTING
    ):
        raise RuntimeError("BLOCKED_PRECONDITION: only local disposable fitflow_test is allowed")


def require_local_test_redis() -> None:
    """Reject non-disposable Redis before any client operation, including under -O."""
    if _cleanup_quarantined:
        raise RuntimeError("BLOCKED_PRECONDITION: test process quarantined after unresolved cleanup")
    try:
        redis_url = urlparse(settings.REDIS_URL or "")
        valid = (
            redis_url.scheme == "redis"
            and redis_url.hostname == "127.0.0.1"
            and redis_url.port == 6379
            and redis_url.path == "/0"
            and redis_url.username is None
            and redis_url.password is None
            and not redis_url.params
            and not redis_url.query
            and not redis_url.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise RuntimeError("BLOCKED_PRECONDITION: only local disposable Redis /0 is allowed")


async def require_postgres15_test_service() -> None:
    """Verify the actual server before fixture writes."""
    require_local_test_database()
    async with AsyncSessionLocal() as probe:
        version = int(await probe.scalar(text("SHOW server_version_num")))
    if not 150000 <= version < 160000:
        raise RuntimeError("BLOCKED_PRECONDITION: PostgreSQL 15 test service required")


async def finish_synthetic_cleanup(work: Awaitable[None]) -> None:
    """Own the original task until terminal, including repeated caller cancellation.

    A soft deadline quarantines the test process, not the task. Never abandon a
    potentially committing coroutine, start a retry, or return to pool disposal
    while it is alive. A stuck task keeps this join blocked; CI's existing job
    deadline bounds the entire disposable service lifetime. On a late terminal
    result or failed cleanup, stop the suite rather than permit further tests.
    """
    global _cleanup_quarantined
    task = asyncio.ensure_future(work)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + _CLEANUP_TIMEOUT_SECONDS
    caller_cancelled = False
    expired = False
    while not task.done():
        remaining = max(0.0, deadline - loop.time())
        if not expired and remaining == 0:
            expired = True
            _cleanup_quarantined = True
        try:
            # asyncio.wait never cancels the original task when its waiter
            # is cancelled or the observation deadline expires.
            await asyncio.wait({task}, timeout=None if expired else remaining)
        except asyncio.CancelledError:
            caller_cancelled = True
    try:
        task.result()  # terminal only; retrieve every exception
    except BaseException as error:
        _cleanup_quarantined = True
        pytest.exit(
            f"BLOCKED_POSTCONDITION: synthetic cleanup terminal error ({type(error).__name__}); "
            "effect not accepted; disposable test process quarantined",
            returncode=1,
        )
    if expired:
        pytest.exit(
            "BLOCKED_POSTCONDITION: cleanup deadline exceeded; original joined; "
            "disposable test process quarantined",
            returncode=1,
        )
    if caller_cancelled:
        raise asyncio.CancelledError


async def cancel_and_join_http_tasks(tasks: Sequence[asyncio.Task]) -> None:
    """Cancel owned HTTP tasks once and join them before fixture deletion."""
    async def join_originals() -> None:
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    await finish_synthetic_cleanup(join_originals())


@asynccontextmanager
async def capture_http_creations(
    *, email: str | None = None, class_name: str | None = None,
) -> AsyncIterator[None]:
    """Track actual ORM INSERT identities in this request scope, never by lookup.

    Mapper after_insert records a successful SQL INSERT before any COMMIT ACK.
    Existing rows or failed unique inserts do not grant deletion authority.
    ContextVar confines collection to the caller and its explicitly joined
    request tasks. Email/name checks only detect collisions/untracked rows.
    """
    require_local_test_database()
    async with AsyncSessionLocal() as db:
        if email is not None and await db.scalar(
            select(User.id).where(User.email == email)
        ) is not None:
            raise RuntimeError("BLOCKED_PRECONDITION: signup marker already exists")
        if class_name is not None and await db.scalar(
            select(GymClass.id).where(GymClass.name == class_name)
        ) is not None:
            raise RuntimeError("BLOCKED_PRECONDITION: catalog marker already exists")

    marker = object()
    users: set[UUID] = set()
    classes: set[UUID] = set()

    def record_user(_mapper, _connection, target: User) -> None:
        if _creation_scope.get() is marker:
            users.add(target.id)

    def record_class(_mapper, _connection, target: GymClass) -> None:
        if _creation_scope.get() is marker:
            classes.add(target.id)

    async def cleanup_and_verify() -> None:
        await cleanup_synthetic_fixture(user_ids=tuple(users), gym_class_ids=tuple(classes))
        async with AsyncSessionLocal() as db:
            if email is not None and await db.scalar(
                select(User.id).where(User.email == email)
            ) is not None:
                raise RuntimeError("BLOCKED_POSTCONDITION: unowned signup marker remains")
            if class_name is not None and await db.scalar(
                select(GymClass.id).where(GymClass.name == class_name)
            ) is not None:
                raise RuntimeError("BLOCKED_POSTCONDITION: unowned catalog marker remains")

    token = _creation_scope.set(marker)
    event.listen(User, "after_insert", record_user)
    try:
        event.listen(GymClass, "after_insert", record_class)
        try:
            yield
        finally:
            event.remove(GymClass, "after_insert", record_class)
    finally:
        event.remove(User, "after_insert", record_user)
        _creation_scope.reset(token)
        await finish_synthetic_cleanup(cleanup_and_verify())


async def cleanup_synthetic_fixture(
    *,
    user_ids: Sequence[UUID],
    class_session_ids: Sequence[UUID] = (),
    class_schedule_ids: Sequence[UUID] = (),
    gym_class_ids: Sequence[UUID] = (),
) -> None:
    """Delete only the newly created fixture identities in FK-safe order."""
    require_local_test_database()
    users = set(user_ids)
    sessions = tuple(class_session_ids)
    schedules = tuple(class_schedule_ids)
    classes = tuple(gym_class_ids)
    async with AsyncSessionLocal() as db:
        for model, ids in ((User, users), (GymClass, classes),
                           (ClassSchedule, schedules), (ClassSession, sessions)):
            if ids:
                await db.execute(select(model.id).where(model.id.in_(ids)).with_for_update())
        # Deletion authority consists ONLY of caller-provided fixture-owned UUIDs.
        # A booking on a synthetic session never makes its owner disposable.
        person_ids = (
            (await db.scalars(select(Person.id).where(Person.user_id.in_(users)).with_for_update())).all()
            if users else []
        )
        # Refuse any cross-scope descendant rather than letting FK CASCADE
        # or SET NULL mutate a retained row. The only implicit dependent roots
        # are profiles, membership, bookings and auth sessions of owned users.
        if person_ids:
            for model in (Client, Teacher):
                await db.execute(select(model.id).where(model.id.in_(person_ids)).with_for_update())
        schedule_links = []
        if classes:
            schedule_links.append(ClassSchedule.gym_class_id.in_(classes))
        if person_ids:
            schedule_links.append(ClassSchedule.teacher_id.in_(person_ids))
        if users:
            schedule_links.extend((ClassSchedule.created_by_id.in_(users),
                                   ClassSchedule.updated_by_id.in_(users)))
        if schedule_links and await db.scalar(
            select(ClassSchedule.id).where(or_(*schedule_links), ClassSchedule.id.not_in(schedules))
        ) is not None:
            raise RuntimeError("BLOCKED_PRECONDITION: cross-scope schedule reference")
        if schedules and await db.scalar(
            select(ClassSession.id).where(
                ClassSession.class_schedule_id.in_(schedules), ClassSession.id.not_in(sessions)
            )
        ) is not None:
            raise RuntimeError("BLOCKED_PRECONDITION: cross-scope class session")
        if sessions and await db.scalar(
            select(Booking.id).where(
                Booking.class_session_id.in_(sessions), Booking.client_id.not_in(person_ids)
            )
        ) is not None:
            raise RuntimeError("BLOCKED_PRECONDITION: retained booking on fixture session")
        dependent_ids = []
        if person_ids:
            for model, foreign_key in ((Booking, Booking.client_id), (Membership, Membership.client_id)):
                dependent_ids.append((model, (await db.scalars(
                    select(model.id).where(foreign_key.in_(person_ids))
                )).all()))
        if users:
            dependent_ids.append((AuthSession, (await db.scalars(
                select(AuthSession.id).where(AuthSession.user_id.in_(users))
            )).all()))
        dependent_ids.extend((model, person_ids) for model in (Client, Teacher, Person))
        if sessions or person_ids:
            predicates = []
            if sessions:
                predicates.append(Booking.class_session_id.in_(sessions))
            if person_ids:
                predicates.append(Booking.client_id.in_(person_ids))
            await db.execute(delete(Booking).where(or_(*predicates)))
        if person_ids:
            await db.execute(delete(Membership).where(Membership.client_id.in_(person_ids)))
        if sessions:
            await db.execute(delete(ClassSession).where(ClassSession.id.in_(sessions)))
        if class_schedule_ids:
            await db.execute(
                delete(ClassSchedule).where(ClassSchedule.id.in_(class_schedule_ids))
            )
        if gym_class_ids:
            await db.execute(delete(GymClass).where(GymClass.id.in_(gym_class_ids)))
        if person_ids:
            await db.execute(delete(Client).where(Client.id.in_(person_ids)))
            await db.execute(delete(Teacher).where(Teacher.id.in_(person_ids)))
            await db.execute(delete(Person).where(Person.id.in_(person_ids)))
        if users:
            await db.execute(delete(AuthSession).where(AuthSession.user_id.in_(users)))
            await db.execute(delete(User).where(User.id.in_(users)))
        await db.commit()
    # An exact postcondition read is not an automatic retry of an uncertain commit.
    async with AsyncSessionLocal() as db:
        for model, ids in dependent_ids:
            if ids and await db.scalar(select(model.id).where(model.id.in_(ids))) is not None:
                raise RuntimeError(f"BLOCKED_POSTCONDITION: owned {model.__name__} remains")
        if users and (await db.scalar(select(User.id).where(User.id.in_(users)))) is not None:
            raise RuntimeError("BLOCKED_POSTCONDITION: synthetic User cleanup incomplete")
        if sessions and (await db.scalar(
            select(ClassSession.id).where(ClassSession.id.in_(sessions))
        )) is not None:
            raise RuntimeError("BLOCKED_POSTCONDITION: synthetic session cleanup incomplete")
        if class_schedule_ids and (await db.scalar(
            select(ClassSchedule.id).where(ClassSchedule.id.in_(class_schedule_ids))
        )) is not None:
            raise RuntimeError("BLOCKED_POSTCONDITION: synthetic schedule cleanup incomplete")
        if gym_class_ids and (await db.scalar(
            select(GymClass.id).where(GymClass.id.in_(gym_class_ids))
        )) is not None:
            raise RuntimeError("BLOCKED_POSTCONDITION: synthetic class cleanup incomplete")
        if users and (await db.scalar(
            select(Person.id).where(Person.user_id.in_(users))
        )) is not None:
            raise RuntimeError("BLOCKED_POSTCONDITION: synthetic person cleanup incomplete")


def staged_access(db: AsyncSession, user_id: UUID, role: str) -> str:
    """Stage a real modern session row; caller commits with synthetic users."""
    require_local_test_database()
    sid = uuid4()
    refresh = create_refresh_token({"sub": str(user_id), "sid": str(sid)})
    family = signed_refresh_family(refresh)
    if family is None or family[0] != sid or family[1] != user_id:
        raise RuntimeError("BLOCKED_PRECONDITION: invalid synthetic signed session")
    db.add(AuthSession(
        id=sid, user_id=user_id, refresh_digest=fingerprint(refresh),
        expires_at=family[2],
    ))
    return create_access_token({"sub": str(user_id), "role": role, "sid": str(sid)})


async def committed_access(user_id: UUID, role: str) -> str:
    """Issue a PG-committed family for an already persisted synthetic user."""
    async with AsyncSessionLocal() as db:
        token = staged_access(db, user_id, role)
        await db.commit()
        return token

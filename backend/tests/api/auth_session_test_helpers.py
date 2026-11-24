"""Exact PostgreSQL SID registration for isolated functional HTTP test credentials.

Never bypass Product authentication. Fixture callers must COMMIT their
current PostgreSQL transaction before using these signed access JWTs.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select
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


def require_local_test_database() -> None:
    """Fail before any synthetic INSERT, even if no bearer will be minted."""
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


async def finish_synthetic_cleanup(work: Awaitable[None]) -> None:
    """Join a scoped cleanup even when its caller receives cancellation.

    Any failure surfaces; never retry an uncertain DB effect implicitly.
    """
    task = asyncio.create_task(work)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 15.0
    cancelled = False
    while not task.done():
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise RuntimeError(
                "BLOCKED_POSTCONDITION: synthetic cleanup still running; reconcile effect"
            )
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=remaining)
        except asyncio.CancelledError:
            # A second (or further) cancellation must not skip the original join.
            cancelled = True
        except TimeoutError as error:
            raise RuntimeError(
                "BLOCKED_POSTCONDITION: synthetic cleanup timeout; reconcile effect"
            ) from error
    # The task may have raised, including a cancellation of its own.
    await task
    if cancelled:
        raise asyncio.CancelledError


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
    async with AsyncSessionLocal() as db:
        # Deletion authority consists ONLY of caller-provided fixture-owned UUIDs.
        # A booking on a synthetic session never makes its owner disposable.
        person_ids = (
            (await db.scalars(select(Person.id).where(Person.user_id.in_(users)))).all()
            if users else []
        )
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

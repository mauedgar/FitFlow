"""IR011: assigned teacher booking scope and safe public catalogue.

Disposable PG15, synthetic account IDs only. All writes are test-owned.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from app.core.config import settings
from app.core.enums import ActivityType, BookingStatus, ClassSessionStatus, UserRole
from app.core.security import create_access_token
from app.db.models.booking import Booking
from app.db.models.class_schedule import ClassSchedule
from app.db.models.class_session import ClassSession
from app.db.models.client import Client
from app.db.models.gym_class import GymClass
from app.db.models.person import Person
from app.db.models.teacher import Teacher
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import delete
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.api, pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(autouse=True)
def disposable_only() -> None:
    assert settings.TESTING is True
    assert make_url(settings.DATABASE_URL).database == "fitflow_test"


@pytest.fixture(autouse=True)
async def release_pool() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture
async def scope() -> AsyncIterator[dict[str, object]]:
    names = ("admin", "front_desk", "teacher_a", "teacher_b", "client")
    accounts = {name: uuid4() for name in names}
    teacher_profiles = (uuid4(), uuid4())
    client_profile, class_id = uuid4(), uuid4()
    schedules = (uuid4(), uuid4())
    sessions = (uuid4(), uuid4())
    bookings = (uuid4(), uuid4())
    day = date.today() + timedelta(days=2)
    begin = datetime.combine(day, time(14, 0), tzinfo=UTC)
    marker = uuid4().hex
    async with AsyncSessionLocal() as db:
        db.add_all([
            User(
                id=accounts[name],
                email=f"ir011-{name}-{marker}@example.com",
                hashed_password="synthetic-no-login", active=True,
                role=UserRole.teacher if name.startswith("teacher") else UserRole(name),
            )
            for name in names
        ])
        await db.commit()
        db.add_all([
            Teacher(
                id=teacher_profiles[i], first_name="Synthetic",
                last_name=f"Teacher{i}", user_id=accounts[f"teacher_{c}"],
            )
            for i, c in enumerate(("a", "b"))
        ] + [Client(
            id=client_profile, first_name="Synthetic", last_name="Client",
            user_id=accounts["client"],
        )])
        db.add(GymClass(
            id=class_id, name=f"IR011 synthetic {marker}",
            description="Scoped booking data", activity_type=ActivityType.group_class,
            duration_minutes=45, default_capacity=9, active=True,
        ))
        await db.commit()
        db.add_all([
            ClassSchedule(
                id=schedules[i], gym_class_id=class_id, teacher_id=teacher_profiles[i],
                rrule="RRULE:FREQ=WEEKLY;COUNT=2",
                start_date=day, start_time=time(11 + i, 0),
                duration_minutes=45, capacity=9, active=True,
            )
            for i in range(2)
        ])
        await db.commit()
        db.add_all([
            ClassSession(
                id=sessions[i], class_schedule_id=schedules[i],
                starts_at=begin + timedelta(hours=i),
                ends_at=begin + timedelta(hours=i, minutes=45),
                capacity_snapshot=9, status=ClassSessionStatus.scheduled, active=True,
            )
            for i in range(2)
        ])
        await db.commit()
        db.add_all([
            Booking(
                id=bookings[i], class_session_id=sessions[i],
                client_id=client_profile, status=BookingStatus.confirmed, active=True,
            )
            for i in range(2)
        ])
        await db.commit()
    try:
        yield {
            "accounts": accounts, "teacher_profiles": teacher_profiles,
            "class_id": class_id, "schedules": schedules, "sessions": sessions,
            "bookings": bookings, "day": day,
        }
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Booking).where(Booking.id.in_(bookings)))
            await db.execute(delete(ClassSession).where(ClassSession.id.in_(sessions)))
            await db.execute(delete(ClassSchedule).where(ClassSchedule.id.in_(schedules)))
            await db.execute(delete(GymClass).where(GymClass.id == class_id))
            await db.execute(delete(Teacher).where(Teacher.id.in_(teacher_profiles)))
            await db.execute(delete(Client).where(Client.id == client_profile))
            await db.execute(delete(Person).where(
                Person.id.in_([*teacher_profiles, client_profile]),
            ))
            await db.execute(delete(User).where(User.id.in_(list(accounts.values()))))
            await db.commit()


def bearer(scope: dict[str, object], who: str) -> dict[str, str]:
    ids: dict[str, UUID] = scope["accounts"]  # type: ignore[assignment]
    role = UserRole.teacher if who.startswith("teacher") else UserRole(who)
    token = create_access_token({"sub": str(ids[who]), "role": role.value})
    return {"Authorization": f"Bearer {token}"}


def ids(response: httpx.Response) -> set[str]:
    assert response.status_code == 200, response.text
    return {row["id"] for row in response.json()}


async def test_ir011_teacher_booking_reads_are_assignment_scoped_before_pagination(
    api_client: httpx.AsyncClient, scope: dict[str, object],
) -> None:
    klass: UUID = scope["class_id"]  # type: ignore[assignment]
    schedules: tuple[UUID, UUID] = scope["schedules"]  # type: ignore[assignment]
    sessions: tuple[UUID, UUID] = scope["sessions"]  # type: ignore[assignment]
    bookings: tuple[UUID, UUID] = scope["bookings"]  # type: ignore[assignment]
    day: date = scope["day"]  # type: ignore[assignment]
    base = f"{settings.API_V1_STR}/bookings"
    endpoints = [
        f"{base}/sessions/{sessions[0]}/public",
        f"{base}/classes/{klass}/public",
        f"{base}/class-schedules/{schedules[0]}/public",
        f"{base}/day?date_query={day}",
        f"{base}/range?date_from={day}&date_to={day}",
    ]
    for url in endpoints:
        only_own = await api_client.get(url, headers=bearer(scope, "teacher_a"))
        assert ids(only_own) == {str(bookings[0])}
        assert (await api_client.get(url)).status_code == 401
        assert (await api_client.get(url, headers=bearer(scope, "client"))).status_code == 403

    for kind, identifier in (("sessions", sessions[1]), ("class-schedules", schedules[1])):
        foreign = await api_client.get(
            f"{base}/{kind}/{identifier}/public", headers=bearer(scope, "teacher_a"),
        )
        assert foreign.status_code == 403, foreign.text
    other = await api_client.get(
        f"{base}/classes/{klass}/public", headers=bearer(scope, "teacher_b"),
    )
    assert ids(other) == {str(bookings[1])}
    for who in ("admin", "front_desk"):
        all_bookings = await api_client.get(
            f"{base}/classes/{klass}/public", headers=bearer(scope, who),
        )
        assert ids(all_bookings) == {str(b) for b in bookings}


async def test_ir011_public_catalogue_and_operational_reads_are_separated(
    api_client: httpx.AsyncClient, scope: dict[str, object],
) -> None:
    klass: UUID = scope["class_id"]  # type: ignore[assignment]
    schedules: tuple[UUID, UUID] = scope["schedules"]  # type: ignore[assignment]
    prefix = settings.API_V1_STR
    for path in ("/gym-classes/", "/class-schedules/"):
        assert (await api_client.get(prefix + path)).status_code == 401
        assert (
            await api_client.get(prefix + path, headers=bearer(scope, "client"))
        ).status_code == 403
    assert (
        await api_client.get(prefix + "/gym-classes/", headers=bearer(scope, "teacher_a"))
    ).status_code == 403
    for who in ("admin", "front_desk"):
        assert str(klass) in ids(
            await api_client.get(
                prefix + "/gym-classes/",
                headers=bearer(scope, who),
                params={"search": "IR011 synthetic", "limit": 200},
            )
        )
        schedule_ids = ids(
            await api_client.get(
                prefix + "/class-schedules/",
                headers=bearer(scope, who),
                params={"gym_class_id": str(klass)},
            )
        )
        assert {str(s) for s in schedules}.issubset(schedule_ids)

    teacher_a = ids(await api_client.get(
        prefix + "/class-schedules/",
        headers=bearer(scope, "teacher_a"),
        params={"gym_class_id": str(klass)},
    ))
    assert str(schedules[0]) in teacher_a and str(schedules[1]) not in teacher_a
    teacher_b = ids(await api_client.get(
        prefix + "/class-schedules/",
        headers=bearer(scope, "teacher_b"),
        params={"gym_class_id": str(klass)},
    ))
    assert str(schedules[1]) in teacher_b and str(schedules[0]) not in teacher_b
    assert (await api_client.get(
        prefix + f"/class-schedules/{schedules[1]}",
        headers=bearer(scope, "teacher_a"),
    )).status_code == 403
    assert (await api_client.get(
        prefix + f"/class-schedules/{schedules[0]}",
        headers=bearer(scope, "teacher_a"),
    )).status_code == 200

    public_classes = await api_client.get(prefix + "/gym-classes/public")
    assert public_classes.status_code == 200, public_classes.text
    public_detail = await api_client.get(prefix + f"/gym-classes/{klass}/public")
    assert public_detail.status_code == 200, public_detail.text
    found = public_detail.json()
    assert found["id"] == str(klass)
    for field in ("created_at", "updated_at", "deleted_at", "class_schedules"):
        assert field not in found
    public_sched = await api_client.get(
        prefix + f"/class-schedules/class/{klass}/public",
    )
    assert {str(s) for s in schedules}.issubset(ids(public_sched))

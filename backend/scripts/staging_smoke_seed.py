"""Reset the bounded staging smoke fixture and recreate its prerequisites."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from app.core.config import settings
from app.core.enums import (
    ActivityType,
    AllowedPlan,
    ClassSessionStatus,
    DifficultyLevel,
    MembershipPlan,
    MembershipStatus,
    UserRole,
)
from app.core.security import get_password_hash
from app.core.timezone import LOCAL_TZ
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
from app.db.session import AsyncSessionLocal, engine
from sqlalchemy import delete

CLIENT_USER_ID = UUID("00000000-0000-4000-8000-000000000101")
CLIENT_ID = UUID("00000000-0000-4000-8000-000000000102")
TEACHER_USER_ID = UUID("00000000-0000-4000-8000-000000000201")
TEACHER_ID = UUID("00000000-0000-4000-8000-000000000202")
FRONT_DESK_USER_ID = UUID("00000000-0000-4000-8000-000000000301")
GYM_CLASS_ID = UUID("00000000-0000-4000-8000-000000000401")
SCHEDULE_ID = UUID("00000000-0000-4000-8000-000000000402")
SESSION_ID = UUID("00000000-0000-4000-8000-000000000403")
MEMBERSHIP_ID = UUID("00000000-0000-4000-8000-000000000501")

CLIENT_EMAIL = "m4-wave-b-client@example.com"
TEACHER_EMAIL = "m4-wave-b-teacher@example.com"
FRONT_DESK_EMAIL = "m4-wave-b-front-desk@example.com"
SMOKE_PASSWORD = "FitFlow-Smoke-Only-2026!"


async def reset_fixture() -> dict[str, str]:
    """Delete only the reserved fixture IDs, then recreate deterministic data."""
    if settings.ENV != "staging":
        raise RuntimeError("Smoke fixture reset is allowed only when ENV=staging.")
    if os.getenv("FITFLOW_SMOKE_ALLOW_FIXTURE_RESET") != "1":
        raise RuntimeError("Set FITFLOW_SMOKE_ALLOW_FIXTURE_RESET=1 explicitly.")

    local_tomorrow = datetime.now(LOCAL_TZ).date() + timedelta(days=1)
    starts_at = datetime.combine(local_tomorrow, time(12, 0), tzinfo=LOCAL_TZ).astimezone(UTC)
    ends_at = starts_at + timedelta(hours=1)
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        async with db.begin():
            await db.execute(delete(Booking).where(Booking.client_id == CLIENT_ID))
            await db.execute(delete(ClassSession).where(ClassSession.id == SESSION_ID))
            await db.execute(delete(ClassSchedule).where(ClassSchedule.id == SCHEDULE_ID))
            await db.execute(delete(Membership).where(Membership.id == MEMBERSHIP_ID))
            await db.execute(delete(Client).where(Client.id == CLIENT_ID))
            await db.execute(delete(Teacher).where(Teacher.id == TEACHER_ID))
            await db.execute(delete(Person).where(Person.id.in_([CLIENT_ID, TEACHER_ID])))
            await db.execute(
                delete(User).where(
                    User.id.in_([CLIENT_USER_ID, TEACHER_USER_ID, FRONT_DESK_USER_ID])
                )
            )
            await db.execute(delete(GymClass).where(GymClass.id == GYM_CLASS_ID))

        password_hash = get_password_hash(SMOKE_PASSWORD)
        client_user = User(
            id=CLIENT_USER_ID,
            email=CLIENT_EMAIL,
            hashed_password=password_hash,
            role=UserRole.client,
        )
        teacher_user = User(
            id=TEACHER_USER_ID,
            email=TEACHER_EMAIL,
            hashed_password=password_hash,
            role=UserRole.teacher,
        )
        front_desk_user = User(
            id=FRONT_DESK_USER_ID,
            email=FRONT_DESK_EMAIL,
            hashed_password=password_hash,
            role=UserRole.front_desk,
        )
        client = Client(
            id=CLIENT_ID,
            first_name="Wave B",
            last_name="Client",
            document_number="M4-WAVE-B-SMOKE-CLIENT",
            user=client_user,
        )
        teacher = Teacher(
            id=TEACHER_ID,
            first_name="Wave B",
            last_name="Teacher",
            cuil="M4-WAVE-B-SMOKE-TEACHER",
            user=teacher_user,
        )
        membership = Membership(
            id=MEMBERSHIP_ID,
            client=client,
            plan=MembershipPlan.classes,
            status=MembershipStatus.active,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        gym_class = GymClass(
            id=GYM_CLASS_ID,
            name="M4 Wave B Smoke Class",
            description="Reserved non-production fixture for the staging MVP smoke.",
            activity_type=ActivityType.group_class,
            duration_minutes=60,
            difficulty=DifficultyLevel.beginner,
            default_capacity=5,
        )
        schedule = ClassSchedule(
            id=SCHEDULE_ID,
            gym_class=gym_class,
            teacher=teacher,
            rrule="RRULE:FREQ=DAILY;COUNT=1",
            start_time=time(12, 0),
            duration_minutes=60,
            capacity=5,
            start_date=local_tomorrow,
            end_date=local_tomorrow,
            allowed_plan=AllowedPlan.classes,
        )
        session = ClassSession(
            id=SESSION_ID,
            class_schedule=schedule,
            starts_at=starts_at,
            ends_at=ends_at,
            capacity_snapshot=5,
            status=ClassSessionStatus.scheduled,
        )
        db.add_all([front_desk_user, membership, session])
        await db.commit()

    return {
        "client_id": str(CLIENT_ID),
        "gym_class_id": str(GYM_CLASS_ID),
        "session_id": str(SESSION_ID),
        "starts_at": starts_at.isoformat(),
    }


async def main() -> None:
    try:
        print(json.dumps(await reset_fixture(), sort_keys=True))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

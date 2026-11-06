"""Synthetic ADMIN E2E fixture. Refuses non-CI, nonempty or non-local databases."""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.core import security
from app.core.config import settings
from app.core.enums import ActivityType, DifficultyLevel, UserRole
from app.db.models.client import Client
from app.db.models.gym_class import GymClass
from app.db.models.teacher import Teacher
from app.db.models.user import User
from app.db.session import AsyncSessionLocal, engine


async def main() -> None:
    url = make_url(settings.DATABASE_URL)
    if not (
        os.getenv("CI") == "true"
        and os.getenv("GITHUB_ACTIONS") == "true"
        and os.getenv("FITFLOW_E2E_SYNTHETIC_ONLY") == "1"
        and settings.ENV == "test"
        and settings.TESTING is True
        and url.database == "fitflow_test"
        and url.host in ("127.0.0.1", "localhost")
        and os.getenv("REDIS_URL") == "redis://127.0.0.1:6379/0"
    ):
        raise SystemExit("BLOCKED_PRECONDITION: disposable GitHub Actions test DB is required")

    admin_email = os.environ["FITFLOW_E2E_ADMIN_EMAIL"]
    client_email = os.environ["FITFLOW_E2E_CLIENT_EMAIL"]
    password = os.environ["FITFLOW_E2E_PASSWORD"]
    if not (admin_email.endswith("@example.com") and client_email.endswith("@example.com")):
        raise SystemExit("BLOCKED_PRECONDITION: synthetic identities required")

    async with AsyncSessionLocal() as db:
        if await db.scalar(select(func.count()).select_from(User)) != 0:
            raise SystemExit("BLOCKED_PRECONDITION: fixture refuses nonempty user table")

        admin = User(id=uuid.uuid4(), email=admin_email,
                     hashed_password=security.get_password_hash(password),
                     role=UserRole.admin, active=True)
        client = User(id=uuid.uuid4(), email=client_email,
                      hashed_password=security.get_password_hash(password),
                      role=UserRole.client, active=True)
        trainer = User(id=uuid.uuid4(), email="teacher-fitflow@example.com",
                       hashed_password=security.get_password_hash(password),
                       role=UserRole.teacher, active=True)
        db.add_all((admin, client, trainer))
        await db.flush()
        db.add_all((
            Client(first_name="Cliente", last_name="Sintético", user_id=client.id),
            Teacher(first_name="Profesora", last_name="Sintética", user_id=trainer.id,
                    cuil="20999999999", bio="Fixture descartable"),
            GymClass(name="Clase Sintética E2E", description="Solo prueba de lectura",
                     activity_type=ActivityType.open_gym,
                     duration_minutes=45, difficulty=DifficultyLevel.beginner,
                     default_capacity=10),
        ))
        await db.commit()

    expired = security.create_access_token(
        data={"sub": str(admin.id), "role": UserRole.admin.value},
        expires_delta=timedelta(minutes=-1),
    )
    path = Path("/tmp/fitflow-admin-e2e-expired.jwt")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(expired)
    await engine.dispose()
    print("SYNTHETIC_ADMIN_FIXTURE_CREATED_ONLY_IN_EMPTY_CI_TEST_DATABASE")


if __name__ == "__main__":
    asyncio.run(main())

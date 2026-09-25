"""HTTP contract for Booking current-user access with canonical UUID token subjects."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models import Client, User
from app.db.session import AsyncSessionLocal, engine
from fastapi import status
from sqlalchemy.engine import make_url

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "R006 Booking current-user HTTP contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


async def _client_access_token() -> str:
    token = uuid.uuid4().hex

    async with AsyncSessionLocal() as db:
        user = User(
            email=f"r006-bookings-me-{token}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        )
        client = Client(
            first_name="R006",
            last_name="CanonicalSubject",
            document_number=token,
            user=user,
        )
        db.add(client)
        await db.flush()
        user_id = user.id
        await db.commit()

    return create_access_token(
        {
            "sub": str(user_id),
            "role": UserRole.client.value,
        }
    )


async def test_read_my_bookings_accepts_canonical_user_id_subject(
    api_client: httpx.AsyncClient,
) -> None:
    access_token = await _client_access_token()

    response = await api_client.get(
        f"{settings.API_V1_STR}/bookings/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == []
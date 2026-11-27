"""HTTP contract for Booking current-user access with canonical UUID token subjects."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from app.core.config import settings
from app.core.enums import UserRole
from auth_session_test_helpers import (
    committed_access, require_local_test_database,
    cleanup_synthetic_fixture, finish_synthetic_cleanup,
)
from app.db.models import Client, User
from app.db.session import AsyncSessionLocal, engine
from fastapi import status

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
    require_local_test_database()


@pytest.fixture
async def client_access_token() -> AsyncIterator[str]:
    token = uuid.uuid4().hex
    user_id = uuid.uuid4()
    try:
        async with AsyncSessionLocal() as db:
            user = User(
                id=user_id,
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
        yield await committed_access(user_id, UserRole.client.value)
    finally:
        await finish_synthetic_cleanup(
            cleanup_synthetic_fixture(user_ids=(user_id,))
        )


async def test_read_my_bookings_accepts_canonical_user_id_subject(
    api_client: httpx.AsyncClient, client_access_token: str,
) -> None:
    access_token = client_access_token

    response = await api_client.get(
        f"{settings.API_V1_STR}/bookings/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == []
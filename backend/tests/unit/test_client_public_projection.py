"""Regression coverage for the ClientPublic read contract.

No database, credentials or external services are required.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.db.models import Client, User
from app.routers import clients as clients_router
from app.services.client_service import to_client_public
from sqlalchemy.ext.asyncio import AsyncSession


def make_client(*, first_name="Ana", last_name="Gómez") -> Client:
    """Use a real detached ORM entity to exercise the public projection."""
    return Client(
        id=uuid4(),
        first_name=first_name,
        last_name=last_name,
        profile_image_url="https://example.test/avatar.png",
        created_at=datetime(2026, 10, 30, 12, 30, tzinfo=UTC),
        user=User(email="ana@example.test", hashed_password="synthetic-only"),
    )

def test_to_client_public_uses_actual_orm_fields():
    raw = make_client()
    public = to_client_public(raw)

    assert public.id == raw.id
    assert public.full_name == "Ana Gómez"
    assert public.email == "ana@example.test"
    assert public.phone is None
    assert public.avatar_url == raw.profile_image_url
    assert public.created_at == "2026-10-30T12:30:00+00:00"


def test_to_client_public_keeps_optional_values_nullable():
    raw = make_client()
    raw.profile_image_url = None
    # Defensive projection test: intentionally simulate an incomplete ORM row.
    object.__setattr__(raw, "created_at", None)

    public = to_client_public(raw)

    assert public.avatar_url is None
    assert public.created_at is None


@pytest.mark.asyncio
async def test_admin_read_passes_eager_user_option(monkeypatch):
    raw = make_client()
    observed = {}

    async def fake_get_multi_visible(*, db, skip, limit):
        observed.update(db=db, skip=skip, limit=limit)
        return [raw]

    monkeypatch.setattr(clients_router.client, "get_multi_visible", fake_get_multi_visible)
    async with AsyncSession() as db:
        result = await clients_router.read_clients(
            db=db,
            skip=0,
            limit=100,
            current_user=User(email="admin@example.test", hashed_password="synthetic-only"),
        )
        assert observed["db"] is db
    assert (observed["skip"], observed["limit"]) == (0, 100)
    assert result[0].full_name == "Ana Gómez"

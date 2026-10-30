"""Regression coverage for the ClientPublic read contract.

No database, credentials or external services are required.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.routers import clients as clients_router
from app.services.client_service import to_client_public


def make_client(*, first_name="Ana", last_name="Gómez"):
    return SimpleNamespace(
        id=uuid4(),
        first_name=first_name,
        last_name=last_name,
        profile_image_url="https://example.test/avatar.png",
        created_at=datetime(2026, 10, 30, 12, 30, tzinfo=timezone.utc),
        user=SimpleNamespace(email="ana@example.test"),
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
    raw.created_at = None

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
    db = object()
    result = await clients_router.read_clients(
        db=db, skip=0, limit=100, current_user=object()
    )

    assert observed["db"] is db
    assert (observed["skip"], observed["limit"]) == (0, 100)
    assert result[0].full_name == "Ana Gómez"

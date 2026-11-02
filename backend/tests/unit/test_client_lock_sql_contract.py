"""SQL compilation regression for Client account/profile row locks.

No database, credentials or SQL execution are involved.
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.crud.crud_client import client
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_client_profile_lock_targets_remain_user_person_client(monkeypatch):
    statements: list[str] = []

    async def capture_execute(statement):
        statements.append(str(statement.compile(dialect=postgresql.dialect())))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))

    async with AsyncSession() as session:
        monkeypatch.setattr(session, "execute", capture_execute)
        result = await client.get_with_relations(
            session, client_id=uuid4(), for_update=True
        )

    assert result is None
    assert len(statements) == 1
    assert "FOR UPDATE OF users, persons, clients" in statements[0]


@pytest.mark.asyncio
async def test_client_profile_read_does_not_lock_without_request(monkeypatch):
    statements: list[str] = []

    async def capture_execute(statement):
        statements.append(str(statement.compile(dialect=postgresql.dialect())))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(first=lambda: None))

    async with AsyncSession() as session:
        monkeypatch.setattr(session, "execute", capture_execute)
        result = await client.get_with_relations(
            session, client_id=uuid4(), for_update=False
        )

    assert result is None
    assert len(statements) == 1
    assert "FOR UPDATE" not in statements[0]

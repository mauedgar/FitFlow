"""R006 fixture reset ownership checks: synthetic collisions always fail closed."""
from __future__ import annotations

from uuid import UUID

import pytest

from scripts import staging_smoke_seed as smoke


class FakeRows:
    def __init__(self, rows: list[tuple]):
        self._rows = rows

    def all(self) -> list[tuple]:
        return self._rows


class ReadOnlyDb:
    def __init__(self, bookings: list[tuple] | None = None):
        self.bookings = bookings or []
        self.statements: list[str] = []

    async def execute(self, statement):  # noqa: ANN001, ANN201
        sql = str(statement)
        self.statements.append(sql)
        return FakeRows(self.bookings if "FROM bookings" in sql else [])


@pytest.mark.asyncio
async def test_empty_fixture_is_read_only() -> None:
    db = ReadOnlyDb()
    await smoke.assert_fixture_ownership(db)
    assert len(db.statements) == 8
    assert all(sql.lstrip().startswith("SELECT ") for sql in db.statements)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("client_id", "session_id"),
    [
        (smoke.CLIENT_ID, UUID("00000000-0000-4000-8000-000000000999")),
        (UUID("00000000-0000-4000-8000-000000000998"), smoke.SESSION_ID),
    ],
)
async def test_cross_fixture_booking_collisions_refused(client_id: UUID, session_id: UUID) -> None:
    db = ReadOnlyDb([(client_id, session_id)])
    with pytest.raises(RuntimeError, match="Unowned booking"):
        await smoke.assert_fixture_ownership(db)
    assert all(sql.lstrip().startswith("SELECT ") for sql in db.statements)


@pytest.mark.asyncio
async def test_only_own_fixture_booking_permitted() -> None:
    db = ReadOnlyDb([(smoke.CLIENT_ID, smoke.SESSION_ID)])
    await smoke.assert_fixture_ownership(db)


@pytest.mark.asyncio
async def test_foreign_reserved_user_id_refused_before_delete() -> None:
    class ForeignUserDb(ReadOnlyDb):
        async def execute(self, statement):  # noqa: ANN001, ANN201
            self.statements.append(str(statement))
            return FakeRows([(smoke.CLIENT_USER_ID, "unrelated@example.com", smoke.UserRole.client)])
    db = ForeignUserDb()
    with pytest.raises(RuntimeError, match="Unowned user/email"):
        await smoke.assert_fixture_ownership(db)
    assert len(db.statements) == 1

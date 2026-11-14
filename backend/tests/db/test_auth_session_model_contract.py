"""G2-A1 metadata and service contract: no retained database required."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import AuthSession, Base
from app.services.auth_session_service import stage_new_session

pytestmark = pytest.mark.unit


def test_explicit_metadata_contains_session_table_with_correct_fk() -> None:
    table = Base.metadata.tables["auth_sessions"]
    assert table is AuthSession.__table__
    assert len(table.primary_key.columns) == 1
    assert table.c.sid.primary_key
    foreign_keys = list(table.c.user_id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "users.id"
    assert foreign_keys[0].ondelete == "RESTRICT"
    assert not table.c.user_id.unique


def test_schema_has_bytea_digests_and_precise_expiry_constraints() -> None:
    ddl = str(CreateTable(AuthSession.__table__).compile(dialect=postgresql.dialect()))
    assert "auth_sessions" in ddl
    assert "BYTEA" in ddl
    assert "logout_proof_expires_at = absolute_expires_at + INTERVAL '24 hours'" in ddl
    assert "octet_length(refresh_credential_digest) = 32" in ddl
    assert "octet_length(logout_proof_digest) = 32" in ddl
    assert "receipt_key_version IS NULL" in ddl
    assert "refresh_generation >= 0" in ddl
    assert set(AuthSession.__table__.indexes)  # Both A1 indexes are registered.
    assert {x.name for x in AuthSession.__table__.indexes} == {
        "ix_auth_sessions_user_created", "ix_auth_sessions_proof_expires"
    }


class FakeAsyncDB:
    def __init__(self) -> None:
        self.added: list[AuthSession] = []
        self.flushes = 0

    def add(self, record: AuthSession) -> None:
        self.added.append(record)

    async def flush(self) -> None:
        self.flushes += 1


@pytest.mark.asyncio
async def test_storage_service_stages_but_never_commits_or_issues_jwt() -> None:
    db = FakeAsyncDB()
    now = datetime.now(UTC)
    record = await stage_new_session(  # type: ignore[arg-type]
        db,
        sid=uuid.uuid4(),
        user_id=uuid.uuid4(),
        refresh_credential_digest=b"r" * 32,
        logout_proof_digest=b"l" * 32,
        logout_proof_key_id="test-only-v1",
        absolute_expires_at=now + timedelta(days=7),
        logout_proof_expires_at=now + timedelta(days=8),
    )
    assert db.added == [record]
    assert db.flushes == 1
    assert record.revoked_at is None
    assert record.last_logout_operation_digest is None
    assert record.receipt_key_version is None


@pytest.mark.asyncio
@pytest.mark.parametrize("field,bad", [
    ("refresh_credential_digest", b"short"),
    ("logout_proof_digest", b""),
    ("logout_proof_digest", b"z" * 33),
])
async def test_stage_rejects_malformed_digest(field: str, bad: bytes) -> None:
    now = datetime.now(UTC)
    kwargs = {
        "sid": uuid.uuid4(), "user_id": uuid.uuid4(),
        "refresh_credential_digest": b"r" * 32,
        "logout_proof_digest": b"l" * 32,
        "logout_proof_key_id": "synthetic", "absolute_expires_at": now + timedelta(days=7),
        "logout_proof_expires_at": now + timedelta(days=8),
    }
    kwargs[field] = bad
    with pytest.raises(ValueError, match="32 digest bytes"):
        await stage_new_session(FakeAsyncDB(), **kwargs)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_stage_rejects_naive_expiry_and_empty_kid() -> None:
    now = datetime.now(UTC)
    kwargs = {
        "sid": uuid.uuid4(), "user_id": uuid.uuid4(),
        "refresh_credential_digest": b"r" * 32,
        "logout_proof_digest": b"l" * 32,
        "logout_proof_key_id": "synthetic", "absolute_expires_at": now + timedelta(days=7),
        "logout_proof_expires_at": now + timedelta(days=8),
    }
    with pytest.raises(ValueError, match="nonempty"):
        await stage_new_session(FakeAsyncDB(), **{**kwargs, "logout_proof_key_id": " "})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        await stage_new_session(
            FakeAsyncDB(), **{**kwargs, "absolute_expires_at": datetime(2026, 11, 13)}
        )  # type: ignore[arg-type]

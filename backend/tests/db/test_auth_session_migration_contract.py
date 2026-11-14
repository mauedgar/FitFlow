"""G2-A1 PostgreSQL15 failpoints; only runs against the disposable fitflow_test DB.

The preexisting deterministic Actions workflow runs `alembic upgrade head`
against the pinned PostgreSQL15 service before pytest. Never run on retained DBs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, delete, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def disposable_engine():
    url = make_url(settings.DATABASE_URL)
    assert url.get_backend_name() == "postgresql"
    assert url.database == "fitflow_test", "REFUSE to touch non-disposable PostgreSQL DB"
    assert url.host in {"127.0.0.1", "localhost", "postgres"}, "REFUSE unknown PostgreSQL host"
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            revision = conn.scalar(text("SELECT version_num FROM alembic_version"))
            assert revision == "a6b7c8d9e0f1", "Run isolated alembic upgrade head first"
            assert conn.scalar(text("SELECT to_regclass('auth_sessions')")) is not None
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def populated(disposable_engine):
    """Use a rollback-only transaction with fully synthetic user and session."""
    conn = disposable_engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
    user_id, sid = uuid.uuid4(), uuid.uuid4()
    now = datetime.now(UTC)
    session.add(User(
        id=user_id, email=f"a1-{user_id.hex}@example.invalid",
        hashed_password="synthetic-not-for-login", role=UserRole.admin, active=True,
    ))
    session.flush()
    session.add(AuthSession(
        sid=sid, user_id=user_id, refresh_generation=0,
        refresh_credential_digest=b"r" * 32,
        logout_proof_digest=b"l" * 32,
        logout_proof_key_id="synthetic-kid",
        absolute_expires_at=now + timedelta(days=7),
        logout_proof_expires_at=now + timedelta(days=8),
    ))
    session.flush()
    try:
        yield session, sid, user_id
    finally:
        session.close()
        outer.rollback()
        conn.close()


def assert_rejected(session: Session, statement) -> None:
    with pytest.raises((IntegrityError, DBAPIError)):
        with session.begin_nested():
            session.execute(statement)
            session.flush()


def test_migration_installs_separate_update_and_delete_guards(disposable_engine) -> None:
    with disposable_engine.connect() as conn:
        triggers = {x[0] for x in conn.execute(text("""
            SELECT tgname FROM pg_trigger
            WHERE tgrelid = 'auth_sessions'::regclass AND NOT tgisinternal
        """))}
        assert "fitflow_auth_sessions_before_update_v1" in triggers
        assert "fitflow_auth_sessions_before_delete_v1" in triggers
        index_names = {r[0] for r in conn.execute(text("""
            SELECT indexname FROM pg_indexes WHERE tablename = 'auth_sessions'
        """))}
        assert {"ix_auth_sessions_user_created", "ix_auth_sessions_proof_expires"} <= index_names


def test_atomic_refresh_and_reject_malformed_rotation(populated) -> None:
    db, sid, _ = populated
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        refresh_credential_digest=b"x" * 32
    ))
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        refresh_generation=1
    ))
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        refresh_generation=9223372036854775807, refresh_credential_digest=b"x" * 32
    ))
    db.execute(update(AuthSession).where(AuthSession.sid == sid).values(
        refresh_generation=1, refresh_credential_digest=b"x" * 32
    ))
    db.flush()
    assert db.scalar(select(AuthSession.refresh_generation).where(AuthSession.sid == sid)) == 1


def test_revocation_receipt_write_once_and_refresh_forbidden(populated) -> None:
    db, sid, _ = populated
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        revoked_at=datetime.now(UTC)
    ))
    db.execute(update(AuthSession).where(AuthSession.sid == sid).values(
        revoked_at=datetime.now(UTC),
        last_logout_operation_digest=b"o" * 32, receipt_key_version="test-version",
    ))
    db.flush()
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        refresh_generation=1, refresh_credential_digest=b"x" * 32
    ))
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        revoked_at=None, last_logout_operation_digest=None, receipt_key_version=None
    ))
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        last_logout_operation_digest=b"z" * 32
    ))
    # Idempotent replay is a database read, never a receipt rewrite.
    assert db.scalar(select(AuthSession.revoked_at).where(AuthSession.sid == sid)) is not None


def test_ownership_proof_expiry_and_early_delete_are_immutable(populated) -> None:
    db, sid, user_id = populated
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(user_id=uuid.uuid4()))
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == sid).values(
        logout_proof_expires_at=datetime.now(UTC) + timedelta(days=3)
    ))
    assert_rejected(db, delete(AuthSession).where(AuthSession.sid == sid))
    assert_rejected(db, delete(User).where(User.id == user_id))


def test_delete_allowed_only_after_proof_retention_boundary(populated) -> None:
    db, sid, user_id = populated
    expired = uuid.uuid4()
    date = datetime.now(UTC) - timedelta(days=10)
    db.add(AuthSession(
        sid=expired, user_id=user_id, refresh_generation=0,
        refresh_credential_digest=b"r" * 32, logout_proof_digest=b"l" * 32,
        logout_proof_key_id="synthetic-kid", created_at=date,
        absolute_expires_at=date + timedelta(days=7),
        logout_proof_expires_at=date + timedelta(days=8),
    ))
    db.flush()
    db.execute(delete(AuthSession).where(AuthSession.sid == expired))
    db.flush()
    assert db.scalar(select(AuthSession.sid).where(AuthSession.sid == expired)) is None
    assert db.scalar(select(AuthSession.sid).where(AuthSession.sid == sid)) == sid


def test_expired_row_may_not_be_first_time_revoked(populated) -> None:
    db, _, user_id = populated
    expired = uuid.uuid4()
    date = datetime.now(UTC) - timedelta(days=10)
    db.add(AuthSession(
        sid=expired, user_id=user_id, refresh_generation=0,
        refresh_credential_digest=b"r" * 32, logout_proof_digest=b"l" * 32,
        logout_proof_key_id="synthetic-kid", created_at=date,
        absolute_expires_at=date + timedelta(days=7),
        logout_proof_expires_at=date + timedelta(days=8),
    ))
    db.flush()
    assert_rejected(db, update(AuthSession).where(AuthSession.sid == expired).values(
        revoked_at=datetime.now(UTC), last_logout_operation_digest=b"o" * 32,
        receipt_key_version="test-version"
    ))


def test_reject_wrong_digest_lengths_and_wrong_user_fk(populated) -> None:
    db, _, uid = populated
    now = datetime.now(UTC)
    for kwargs in [
        {"refresh_credential_digest": b"short"},
        {"logout_proof_digest": b"bad"},
        {"logout_proof_key_id": ""},
        {"user_id": uuid.uuid4()},
        {"logout_proof_expires_at": now + timedelta(days=9)},
    ]:
        fields = {
            "sid": uuid.uuid4(), "user_id": uid,
            "refresh_credential_digest": b"r" * 32,
            "logout_proof_digest": b"l" * 32,
            "logout_proof_key_id": "synthetic-kid",
            "absolute_expires_at": now + timedelta(days=7),
            "logout_proof_expires_at": now + timedelta(days=8),
            **kwargs,
        }
        assert_rejected(db, AuthSession.__table__.insert().values(**fields))

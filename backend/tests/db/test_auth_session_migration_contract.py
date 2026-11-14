"""G2-A1 PostgreSQL15 failpoints; only runs against the disposable fitflow_test DB.

The preexisting deterministic Actions workflow runs `alembic upgrade head`
against the pinned PostgreSQL15 service before pytest. Never run on retained DBs.
"""

from __future__ import annotations

import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from threading import Event

from alembic.migration import MigrationContext
from alembic.operations import Operations

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


def test_migration_installs_insert_update_and_delete_guards(disposable_engine) -> None:
    with disposable_engine.connect() as conn:
        triggers = {x[0] for x in conn.execute(text("""
            SELECT tgname FROM pg_trigger
            WHERE tgrelid = 'auth_sessions'::regclass AND NOT tgisinternal
        """))}
        assert "fitflow_auth_sessions_before_insert_v1" in triggers
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


def test_insert_must_start_active_at_generation_zero(populated) -> None:
    db, _, user_id = populated
    now = datetime.now(UTC)
    fields = {
        "user_id": user_id,
        "refresh_generation": 0,
        "refresh_credential_digest": b"r" * 32,
        "logout_proof_digest": b"l" * 32,
        "logout_proof_key_id": "synthetic-kid",
        "absolute_expires_at": now + timedelta(days=7),
        "logout_proof_expires_at": now + timedelta(days=8),
    }
    for invalid in (
        {"refresh_generation": 1},
        {"revoked_at": now, "last_logout_operation_digest": b"o" * 32,
         "receipt_key_version": "synthetic-version"},
        {"last_logout_operation_digest": b"o" * 32},
        {"receipt_key_version": "synthetic-version"},
    ):
        assert_rejected(
            db,
            AuthSession.__table__.insert().values(
                sid=uuid.uuid4(), **{**fields, **invalid}
            ),
        )


def test_future_dated_first_revocation_is_rejected(populated) -> None:
    db, sid, _ = populated
    assert_rejected(
        db,
        update(AuthSession).where(AuthSession.sid == sid).values(
            revoked_at=datetime.now(UTC) + timedelta(seconds=30),
            last_logout_operation_digest=b"o" * 32,
            receipt_key_version="synthetic-version",
        ),
    )


@pytest.fixture
def disposable_lock_probe(disposable_engine):
    """Committed scratch TABLE only on the verified disposable PG15 test DB.

    A rollback-only fixture cannot be seen by an independent connection.
    Clone the real CHECKs and install the real trigger function; DROP in finally.
    No retained auth_sessions or users rows are committed.
    """
    name = f"auth_sessions_lock_probe_{uuid.uuid4().hex}"
    with disposable_engine.begin() as connection:
        connection.exec_driver_sql(f"CREATE TABLE {name} (LIKE auth_sessions INCLUDING ALL)")
        connection.exec_driver_sql(
            f"CREATE TRIGGER fitflow_probe_guard_update BEFORE UPDATE ON {name} "
            "FOR EACH ROW EXECUTE FUNCTION fitflow_auth_sessions_guard_update_v1()"
        )
    try:
        yield name
    finally:
        with disposable_engine.begin() as connection:
            connection.exec_driver_sql(f"DROP TABLE {name}")


def _wait_for_pg_row_lock(engine, pid: int) -> bool:
    """Observe an actual competing PostgreSQL backend blocked on a row lock."""
    for _ in range(40):
        with engine.connect() as observer:
            wait_type = observer.scalar(
                text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :pid"),
                {"pid": pid},
            )
        if wait_type == "Lock":
            return True
        time.sleep(0.05)
    return False


def _competing_update(engine, table: str, sid: uuid.UUID, values: dict, ready: Event,
                      identity: dict) -> tuple[str | None, str]:
    """Return SQLSTATE and message, never classify an unrelated SQL error as PASS."""
    assignments = ", ".join(f"{name} = :{name}" for name in values)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
            identity["pid"] = connection.scalar(text("SELECT pg_backend_pid()"))
            ready.set()
            connection.execute(
                text(f"UPDATE {table} SET {assignments} WHERE sid = :sid"),
                {**values, "sid": sid},
            )
        return None, "UNEXPECTED_SUCCESS"
    except DBAPIError as exc:
        state = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
        return state, str(exc.orig)


def test_competing_rotation_rejects_stale_generation(
    disposable_engine, disposable_lock_probe
) -> None:
    """Two independent transactions cannot both commit generation one."""
    table = disposable_lock_probe
    sid = uuid.uuid4()
    now = datetime.now(UTC)
    with disposable_engine.begin() as connection:
        connection.execute(
            text(f"""
                INSERT INTO {table}
                    (sid, user_id, refresh_generation, refresh_credential_digest,
                     logout_proof_digest, logout_proof_key_id, absolute_expires_at,
                     logout_proof_expires_at)
                VALUES (:sid, :uid, 0, :rd, :ld, 'synthetic-kid', :expiry, :proof)
            """),
            {"sid": sid, "uid": uuid.uuid4(), "rd": b"r" * 32, "ld": b"l" * 32,
             "expiry": now + timedelta(days=7), "proof": now + timedelta(days=8)},
        )
    ready = Event()
    identity = {}
    with disposable_engine.connect() as holder:
        transaction = holder.begin()
        holder.execute(text(f"SELECT sid FROM {table} WHERE sid = :sid FOR UPDATE"),
                       {"sid": sid})
        holder.execute(text(f"""
            UPDATE {table} SET refresh_generation = 1, refresh_credential_digest = :rd
            WHERE sid = :sid
        """), {"sid": sid, "rd": b"x" * 32})
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _competing_update, disposable_engine, table, sid,
                {"refresh_generation": 1, "refresh_credential_digest": b"y" * 32},
                ready, identity,
            )
            try:
                assert ready.wait(3), "Competing DB connection did not start"
                assert _wait_for_pg_row_lock(disposable_engine, identity["pid"])
            finally:
                transaction.commit()
            result = future.result(timeout=6)
    assert result[0] == "23514", result
    assert "auth_session_invalid_refresh_transition" in result[1]
    with disposable_engine.connect() as connection:
        values = connection.execute(
            text(f"SELECT refresh_generation, refresh_credential_digest FROM {table} "
                 "WHERE sid = :sid"), {"sid": sid},
        ).one()
        assert values == (1, b"x" * 32)


def test_competing_expiry_uses_clock_after_row_lock(
    disposable_engine, disposable_lock_probe
) -> None:
    """An UPDATE submitted before expiry must fail if the row unlocks after it."""
    table = disposable_lock_probe
    sid = uuid.uuid4()
    now = datetime.now(UTC)
    expiry = now + timedelta(seconds=3)
    with disposable_engine.begin() as connection:
        connection.execute(
            text(f"""
                INSERT INTO {table}
                    (sid, user_id, refresh_generation, refresh_credential_digest,
                     logout_proof_digest, logout_proof_key_id, absolute_expires_at,
                     logout_proof_expires_at)
                VALUES (:sid, :uid, 0, :rd, :ld, 'synthetic-kid', :expiry, :proof)
            """),
            {"sid": sid, "uid": uuid.uuid4(), "rd": b"r" * 32, "ld": b"l" * 32,
             "expiry": expiry, "proof": expiry + timedelta(hours=24)},
        )
    ready = Event()
    identity = {}
    with disposable_engine.connect() as holder:
        transaction = holder.begin()
        holder.execute(text(f"SELECT sid FROM {table} WHERE sid = :sid FOR UPDATE"),
                       {"sid": sid})
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _competing_update, disposable_engine, table, sid,
                {"revoked_at": datetime.now(UTC),
                 "last_logout_operation_digest": b"o" * 32,
                 "receipt_key_version": "synthetic-version"},
                ready, identity,
            )
            try:
                assert ready.wait(3), "Competing DB connection did not start"
                assert _wait_for_pg_row_lock(disposable_engine, identity["pid"])
                time.sleep(max(0.0, (expiry - datetime.now(UTC)).total_seconds()) + 0.2)
            finally:
                transaction.commit()
            result = future.result(timeout=6)
    assert result[0] == "23514", result
    assert "auth_session_expired_write" in result[1]
    with disposable_engine.connect() as connection:
        assert connection.scalar(text(f"SELECT revoked_at FROM {table} WHERE sid = :sid"),
                                 {"sid": sid}) is None


@pytest.fixture
def exact_migrated_schema_probe(disposable_engine):
    """Run the ACTUAL Alembic A1 upgrade in a fully disposable PG schema.

    This is not a CREATE TABLE LIKE copy: real DDL, all three installed triggers,
    CHECKs, indexes and a real FK (to a synthetic users stub). Two connections
    can see committed synthetic rows. DROP SCHEMA CASCADE cleans everything.
    The qualified fitflow_test DB guard is enforced by disposable_engine.
    """
    schema = f"fitflow_a1_probe_{uuid.uuid4().hex}"
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic" / "versions" / "a6b7c8d9e0f1_auth_sessions_additive.py"
    )
    spec = spec_from_file_location(f"fitflow_a1_probe_{uuid.uuid4().hex}", path)
    assert spec is not None and spec.loader is not None
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    with disposable_engine.begin() as conn:
        conn.exec_driver_sql(f"CREATE SCHEMA {schema}")
        conn.exec_driver_sql(f"CREATE TABLE {schema}.users (id uuid PRIMARY KEY)")
        conn.exec_driver_sql(f"SET LOCAL search_path TO {schema}, public")
        migration.op = Operations(MigrationContext.configure(conn))
        migration.upgrade()
        user_id = uuid.uuid4()
        conn.execute(text(f"INSERT INTO {schema}.users (id) VALUES (:id)"), {"id": user_id})
    try:
        yield f"{schema}.auth_sessions", user_id
    finally:
        with disposable_engine.begin() as conn:
            conn.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")


def test_full_migrated_schema_fk_triggers_and_two_connection_rotation(
    disposable_engine, exact_migrated_schema_probe
) -> None:
    """Prove lock/rotation on an actual migration-installed table + FK."""
    table, user_id = exact_migrated_schema_probe
    sid = uuid.uuid4()
    now = datetime.now(UTC)
    with disposable_engine.begin() as conn:
        triggers = {r[0] for r in conn.execute(text("""
            SELECT tgname FROM pg_trigger
            WHERE tgrelid = to_regclass(:table) AND NOT tgisinternal
        """), {"table": table})}
        assert triggers == {
            "fitflow_auth_sessions_before_insert_v1",
            "fitflow_auth_sessions_before_update_v1",
            "fitflow_auth_sessions_before_delete_v1",
        }
        assert conn.scalar(text("""
            SELECT confdeltype FROM pg_constraint
            WHERE conrelid = to_regclass(:table) AND contype = 'f'
        """), {"table": table}) == "r"
        conn.execute(text(f"""
            INSERT INTO {table}
                (sid, user_id, refresh_generation, refresh_credential_digest,
                 logout_proof_digest, logout_proof_key_id, absolute_expires_at,
                 logout_proof_expires_at)
            VALUES (:sid, :uid, 0, :rd, :ld, 'synthetic-kid', :expiry, :proof)
        """), {"sid": sid, "uid": user_id, "rd": b"r" * 32, "ld": b"l" * 32,
               "expiry": now + timedelta(days=7), "proof": now + timedelta(days=8)})
    ready = Event()
    identity = {}
    with disposable_engine.connect() as holder:
        tx = holder.begin()
        holder.execute(text(f"SELECT sid FROM {table} WHERE sid=:sid FOR UPDATE"),
                       {"sid": sid})
        holder.execute(text(f"""
            UPDATE {table} SET refresh_generation=1, refresh_credential_digest=:digest
            WHERE sid=:sid
        """), {"sid": sid, "digest": b"x" * 32})
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _competing_update, disposable_engine, table, sid,
                {"refresh_generation": 1, "refresh_credential_digest": b"y" * 32},
                ready, identity,
            )
            try:
                assert ready.wait(3)
                assert _wait_for_pg_row_lock(disposable_engine, identity["pid"])
            finally:
                tx.commit()
            state, message = future.result(timeout=6)
    assert state == "23514", (state, message)
    assert "auth_session_invalid_refresh_transition" in message
    with disposable_engine.connect() as conn:
        assert conn.execute(text(f"""
            SELECT refresh_generation, refresh_credential_digest
            FROM {table} WHERE sid=:sid
        """), {"sid": sid}).one() == (1, b"x" * 32)
        with pytest.raises(DBAPIError) as exc:
            with conn.begin_nested():
                conn.execute(text(f"DELETE FROM {table} WHERE sid=:sid"), {"sid": sid})
        assert getattr(exc.value.orig, "sqlstate", None) == "23514"
        assert "auth_session_retention_not_elapsed" in str(exc.value.orig)


def test_full_migrated_schema_expiry_decision_after_lock(
    disposable_engine, exact_migrated_schema_probe
) -> None:
    """One real migration-installed row, lock held across absolute expiry."""
    table, user_id = exact_migrated_schema_probe
    sid = uuid.uuid4()
    now = datetime.now(UTC)
    expiry = now + timedelta(seconds=3)
    with disposable_engine.begin() as conn:
        conn.execute(text(f"""
            INSERT INTO {table}
                (sid, user_id, refresh_generation, refresh_credential_digest,
                 logout_proof_digest, logout_proof_key_id, absolute_expires_at,
                 logout_proof_expires_at)
            VALUES (:sid, :uid, 0, :rd, :ld, 'synthetic-kid', :expiry, :proof)
        """), {"sid": sid, "uid": user_id, "rd": b"r" * 32, "ld": b"l" * 32,
               "expiry": expiry, "proof": expiry + timedelta(hours=24)})
    ready = Event()
    identity = {}
    with disposable_engine.connect() as holder:
        tx = holder.begin()
        holder.execute(text(f"SELECT sid FROM {table} WHERE sid=:sid FOR UPDATE"),
                       {"sid": sid})
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _competing_update, disposable_engine, table, sid,
                {"revoked_at": datetime.now(UTC),
                 "last_logout_operation_digest": b"o" * 32,
                 "receipt_key_version": "synthetic-version"},
                ready, identity,
            )
            try:
                assert ready.wait(3)
                assert _wait_for_pg_row_lock(disposable_engine, identity["pid"])
                time.sleep(max(0.0, (expiry - datetime.now(UTC)).total_seconds()) + 0.2)
            finally:
                tx.commit()
            state, message = future.result(timeout=6)
    assert state == "23514", (state, message)
    assert "auth_session_expired_write" in message
    with disposable_engine.connect() as conn:
        assert conn.scalar(text(f"SELECT revoked_at FROM {table} WHERE sid=:sid"),
                           {"sid": sid}) is None

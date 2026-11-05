"""Isolated fail-closed unit proof for historical Alembic revision f5453ed20cdc.

Does not connect to any database, run Alembic CLI, or touch retained data.
Integration qualification on disposable PostgreSQL remains a separate gate.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.dialects.postgresql import dialect

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions"
    / "f5453ed20cdc_core_domain_refactor.py"
)
spec = importlib.util.spec_from_file_location("fitflow_f5453ed20cdc_guard", MIGRATION_PATH)
assert spec is not None and spec.loader is not None
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

TABLES = [("public", table) for table in migration._CORE_REFACTOR_TARGETS] + [
    ("audit", "external_referencing_table"),
    ("public", "other_data"),
]


class StubConnection:
    def __init__(self, occupied=(), fail_lock=False, catalog=None):
        self.occupied = set(occupied)
        self.fail_lock = fail_lock
        self.catalog = TABLES if catalog is None else catalog
        self.queries = []
        self.dialect = dialect()

    def execute(self, stmt):
        sql = str(stmt).strip()
        self.queries.append(sql)
        if sql.startswith("SET LOCAL"):
            return SimpleNamespace()
        if sql.startswith("LOCK TABLE"):
            if self.fail_lock:
                raise RuntimeError("lock denied")
            return SimpleNamespace()
        if sql.startswith("SELECT schemaname"):
            return SimpleNamespace(all=lambda: self.catalog)
        if sql.startswith("SELECT EXISTS"):
            qualified = sql.split("FROM ")[1].split(")")[0]
            return SimpleNamespace(scalar_one=lambda: qualified in self.occupied)
        raise AssertionError(f"Unexpected SQL: {sql}")


@pytest.mark.unit
def test_empty_revision_inputs_lock_before_reading_all_user_tables():
    conn = StubConnection()
    migration._require_empty_core_domain_refactor_inputs(conn)
    assert conn.queries[0].startswith("SET LOCAL lock_timeout")
    assert conn.queries[1].startswith("LOCK TABLE teacher_class_association")
    assert "IN ACCESS EXCLUSIVE MODE" in conn.queries[1]
    assert len([q for q in conn.queries if q.startswith("SELECT EXISTS")]) == len(TABLES)
    assert 'SELECT EXISTS (SELECT 1 FROM "audit"."external_referencing_table")' in conn.queries


@pytest.mark.unit
@pytest.mark.parametrize("schema,table", TABLES)
def test_any_retained_table_blocks_destructive_upgrade_before_ddl(
    monkeypatch, schema, table,
):
    conn = StubConnection([f'"{schema}"."{table}"'])
    monkeypatch.setattr(migration.op, "get_bind", lambda: conn)
    with pytest.raises(RuntimeError, match="refuses to discard retained Product data"):
        migration.upgrade()
    assert conn.queries[1].startswith("LOCK TABLE")
    assert not any("TRUNCATE TABLE" in q or "DROP TABLE" in q for q in conn.queries)


@pytest.mark.unit
def test_lock_conflict_fails_closed(monkeypatch):
    conn = StubConnection(fail_lock=True)
    monkeypatch.setattr(migration.op, "get_bind", lambda: conn)
    with pytest.raises(RuntimeError, match="lock denied"):
        migration.upgrade()
    assert len(conn.queries) == 2


@pytest.mark.unit
def test_unknown_catalog_fails_closed():
    conn = StubConnection(catalog=[])
    with pytest.raises(RuntimeError, match="could not inspect user tables"):
        migration._require_empty_core_domain_refactor_inputs(conn)

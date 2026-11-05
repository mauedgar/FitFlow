"""Isolated AST-extracted unit proof for Alembic f5453ed20cdc safety.

The repo has a local backend/alembic package that shadows installed Alembic
under pytest. Compile the exact guard AST without importing the migration
module; no real database, migration or DDL is executed by this unit test.
"""
import ast
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import dialect

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "alembic" / "versions"
    / "f5453ed20cdc_core_domain_refactor.py"
)
source = ast.parse(MIGRATION_PATH.read_text(encoding="utf-8"))
guard_node = next(
    x for x in source.body
    if isinstance(x, ast.FunctionDef) and x.name == "_require_empty_core_domain_refactor_inputs"
)
targets_node = next(
    x for x in source.body
    if isinstance(x, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "_CORE_REFACTOR_TARGETS" for t in x.targets)
)
namespace = {"sa": sa, "time": time}
exec(
    compile(ast.Module(body=[targets_node, guard_node], type_ignores=[]), str(MIGRATION_PATH), "exec"),
    namespace,
)
guard = namespace["_require_empty_core_domain_refactor_inputs"]
targets = namespace["_CORE_REFACTOR_TARGETS"]

RELATIONS = [("public", name, "r") for name in targets] + [
    ("external", "indirect_cascade_child", "r"),
    ("public", "partitioned_parent", "p"),
]


class StubConnection:
    def __init__(self, occupied=(), relations=None, temporary=False, fail_lock=False, current_schema="public", rls_relations=()):
        self.occupied = set(occupied)
        self.current_schema = current_schema
        self.rls_relations = set(rls_relations)
        self.relations = RELATIONS if relations is None else relations
        self.temporary = temporary
        self.fail_lock = fail_lock
        self.dialect = dialect()
        self.sql = []
        self.calls = []

    def execute(self, stmt, params=None):
        sql = str(stmt).strip()
        self.sql.append(sql)
        self.calls.append((sql, params))
        if sql.startswith("SELECT current_setting"):
            return SimpleNamespace(scalar_one=lambda: "0")
        if sql == "SELECT current_schema()":
            return SimpleNamespace(scalar_one=lambda: self.current_schema)
        if sql.startswith("SELECT set_config") or sql.startswith("SET LOCAL"):
            return SimpleNamespace()
        if sql.startswith("LOCK TABLE"):
            if self.fail_lock:
                raise RuntimeError("lock denied")
            return SimpleNamespace()
        if sql.startswith("SELECT EXISTS"):
            if "pg_my_temp_schema()" in sql:
                return SimpleNamespace(scalar_one=lambda: self.temporary)
            qualified = sql.split("FROM ")[1].split(")")[0]
            return SimpleNamespace(scalar_one=lambda: qualified in self.occupied)
        if sql.startswith("SELECT n.nspname"):
            return SimpleNamespace(all=lambda: self.relations)
        if sql.startswith("SELECT c.relrowsecurity"):
            qualified = (params["schema"], params["name"])
            return SimpleNamespace(
                one_or_none=lambda: (qualified in self.rls_relations, False)
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


@pytest.mark.unit
def test_guard_is_first_upgrade_effect_before_enum_or_drop():
    upgrade = next(
        x for x in source.body if isinstance(x, ast.FunctionDef) and x.name == "upgrade"
    )
    assert isinstance(upgrade.body[0], ast.Assign)
    assert isinstance(upgrade.body[1], ast.Expr)
    call = upgrade.body[1].value
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name)
    assert call.func.id == "_require_empty_core_domain_refactor_inputs"


@pytest.mark.unit
def test_empty_migration_inputs_lock_targets_before_enumerating_all_relations():
    conn = StubConnection()
    guard(conn)
    assert conn.sql[0] == "SELECT current_schema()"
    assert conn.sql[3].startswith("SET LOCAL lock_timeout")
    assert conn.sql[5].startswith('LOCK TABLE "public"."teacher_class_association"')
    assert "IN ACCESS EXCLUSIVE MODE" in conn.sql[3]
    assert len([q for q in conn.sql if q.startswith("SELECT EXISTS (SELECT 1 FROM")]) == len(RELATIONS)


@pytest.mark.unit
@pytest.mark.parametrize("schema,name,kind", RELATIONS)
def test_any_retained_user_table_blocks_destructive_upgrade(schema, name, kind):
    conn = StubConnection({f'"{schema}"."{name}"'})
    with pytest.raises(RuntimeError, match="refuses to discard retained Product data"):
        guard(conn)
    assert not any("TRUNCATE TABLE" in q or "DROP TABLE" in q for q in conn.sql)


@pytest.mark.unit
@pytest.mark.parametrize("kind", ["f", "m"])
def test_foreign_and_materialized_relations_refused_without_scanning_remote_data(kind):
    conn = StubConnection(relations=[("external", "unsupported_relation", kind)])
    with pytest.raises(RuntimeError, match="unsupported relation"):
        guard(conn)


@pytest.mark.unit
def test_local_temporary_relation_fails_closed():
    with pytest.raises(RuntimeError, match="temporary relations"):
        guard(StubConnection(temporary=True))


@pytest.mark.unit
def test_lock_failure_fails_closed_before_ddl():
    with pytest.raises(RuntimeError, match="lock denied"):
        guard(StubConnection(fail_lock=True))


@pytest.mark.unit
def test_missing_catalog_fails_closed():
    with pytest.raises(RuntimeError, match="could not inspect user relations"):
        guard(StubConnection(relations=[]))


@pytest.mark.unit
def test_deadline_exhaustion_is_a_fail_closed_result(monkeypatch):
    values = iter([100.0, 121.0])
    monkeypatch.setattr(time, "monotonic", lambda: next(values))
    with pytest.raises(RuntimeError, match="time budget exceeded"):
        guard(StubConnection())


@pytest.mark.unit
@pytest.mark.parametrize("schema", ["pg_catalog", "custom", None])
def test_nonpublic_search_path_fails_closed_before_any_lock(schema):
    conn = StubConnection(current_schema=schema)
    with pytest.raises(RuntimeError, match="requires public schema"):
        guard(conn)
    assert conn.sql == ["SELECT current_schema()"]


@pytest.mark.unit
def test_rls_enabled_table_refused_before_occupancy_check():
    conn = StubConnection(rls_relations={("public", "gym_classes")})
    with pytest.raises(RuntimeError, match="refuses RLS-enabled relation"):
        guard(conn)
    assert not any("TRUNCATE TABLE" in q or "DROP TABLE" in q for q in conn.sql)
    assert 'SELECT EXISTS (SELECT 1 FROM "public"."gym_classes")' not in conn.sql


@pytest.mark.unit
def test_successful_guard_restores_transaction_local_timeouts():
    conn = StubConnection()
    guard(conn)
    assert conn.calls[-2] == (
        "SELECT set_config('statement_timeout', :value, true)", {"value": "0"}
    )
    assert conn.calls[-1] == (
        "SELECT set_config('lock_timeout', :value, true)", {"value": "0"}
    )

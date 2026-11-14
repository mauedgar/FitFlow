"""G2-A1 disposable-only retention-index EXPLAIN evidence.

This qualifies index eligibility, NOT production query latency, erasure policy,
auth A2, signed receipts, committed logout or any retained migration.
Runs only inside a synthetic GitHub Actions PostgreSQL15 service.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, insert, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole
from app.db.models.auth_session import AuthSession
from app.db.models.user import User

pytestmark = pytest.mark.integration

_INDEX = "ix_auth_sessions_proof_expires"


def _has_index_name(plan: object, index_name: str) -> bool:
    if isinstance(plan, dict):
        if plan.get("Index Name") == index_name:
            return True
        return any(_has_index_name(part, index_name) for part in plan.values())
    if isinstance(plan, list):
        return any(_has_index_name(part, index_name) for part in plan)
    return False


def _json_plan(value: object) -> object:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    return json.loads(value) if isinstance(value, str) else value


def test_retention_index_eligible_on_disposable_pg15() -> None:
    """Use actual A1 migration/index and rolled-back representative synthetic rows."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        pytest.skip("Source-only outside the original disposable Actions runner")

    url = make_url(settings.DATABASE_URL)
    assert url.get_backend_name() == "postgresql"
    assert url.database == "fitflow_test"
    assert url.host in {"127.0.0.1", "localhost", "postgres"}
    assert url.username == "fitflow_test_user", "Refusing non-disposable DB principal"

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    connection = None
    outer = None
    session = None
    try:
        connection = engine.connect()
        outer = connection.begin()
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "a6b7c8d9e0f1", "A1 migration must be installed in disposable CI"
        assert connection.scalar(text("SELECT to_regclass('auth_sessions')")) is not None
        index_names = {
            row[0] for row in connection.execute(
                text("SELECT indexname FROM pg_indexes "
                     "WHERE schemaname = current_schema() AND tablename = 'auth_sessions'")
            )
        }
        assert _INDEX in index_names

        session = Session(
            bind=connection, join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        user_id = uuid.uuid4()
        session.add(
            User(
                id=user_id,
                email=f"a1-index-{user_id.hex}@example.invalid",
                hashed_password="synthetic-not-for-login",
                role=UserRole.admin,
                active=True,
            )
        )
        session.flush()

        now = datetime.now(UTC)
        past_created = now - timedelta(days=20)
        past_expiry = now - timedelta(days=10)
        future_expiry = now + timedelta(days=7)
        rows = []
        for i in range(2400):
            expires_at = past_expiry if i < 24 else future_expiry
            rows.append(
                {
                    "sid": uuid.uuid4(),
                    "user_id": user_id,
                    "refresh_generation": 0,
                    "refresh_credential_digest": b"r" * 32,
                    "logout_proof_digest": b"l" * 32,
                    "logout_proof_key_id": "synthetic-index-only",
                    "created_at": past_created if i < 24 else now,
                    "absolute_expires_at": expires_at,
                    "logout_proof_expires_at": expires_at + timedelta(hours=24),
                }
            )
        session.execute(insert(AuthSession.__table__), rows)
        assert session.scalar(
            text("SELECT count(*) FROM auth_sessions "
                 "WHERE logout_proof_expires_at < :cutoff"),
            {"cutoff": now},
        ) >= 24

        # On ephemeral CI only. Planner statistics are NOT production benchmarks.
        session.execute(text("ANALYZE auth_sessions"))
        query = text(
            "EXPLAIN (FORMAT JSON) SELECT sid FROM auth_sessions "
            "WHERE logout_proof_expires_at < :cutoff"
        )
        natural_plan = _json_plan(session.execute(query, {"cutoff": now}).scalar_one())
        session.execute(text("SET LOCAL enable_seqscan = off"))
        eligible_plan = _json_plan(session.execute(query, {"cutoff": now}).scalar_one())
        assert _has_index_name(eligible_plan, _INDEX), eligible_plan
        print(
            "G2_A1_DISPOSABLE_INDEX_ELIGIBLE",
            json.dumps(
                {
                    "index": _INDEX,
                    "synthetic_rows": len(rows),
                    "natural_plan": natural_plan,
                    "index_eligible_plan": eligible_plan,
                    "persistent_data_effect": "NONE_ROLLBACK_ONLY",
                    "production_latency_qualified": False,
                },
                default=str, sort_keys=True,
            ),
        )
    finally:
        if session is not None:
            session.close()
        if outer is not None and outer.is_active:
            outer.rollback()
        if connection is not None:
            connection.close()
        engine.dispose()

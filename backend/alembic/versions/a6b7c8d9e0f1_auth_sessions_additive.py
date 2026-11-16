"""Add durable per-login auth session rows without activating new auth behavior.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0

G2-A1: additive, empty table. No retained database operation is authorized
by defining this migration. Rollback of durable revocation state is forbidden.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a6b7c8d9e0f1"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None



GUARD_INSERT_SQL = """
CREATE FUNCTION fitflow_auth_sessions_guard_insert_v1()
RETURNS trigger
LANGUAGE plpgsql
AS $fitflow$
BEGIN
    -- New sessions always start ACTIVE at generation zero. A receipt may
    -- only arise from a later, row-locked ACTIVE -> REVOKED transition.
    IF NEW.refresh_generation IS DISTINCT FROM 0
       OR NEW.revoked_at IS NOT NULL
       OR NEW.last_logout_operation_digest IS NOT NULL
       OR NEW.receipt_key_version IS NOT NULL
    THEN
        RAISE EXCEPTION 'auth_session_invalid_initial_state' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$fitflow$
"""


GUARD_UPDATE_SQL = """
CREATE FUNCTION fitflow_auth_sessions_guard_update_v1()
RETURNS trigger
LANGUAGE plpgsql
AS $fitflow$
DECLARE
    decision_clock timestamptz;
BEGIN
    IF NEW.sid IS DISTINCT FROM OLD.sid
       OR NEW.user_id IS DISTINCT FROM OLD.user_id
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.absolute_expires_at IS DISTINCT FROM OLD.absolute_expires_at
       OR NEW.logout_proof_expires_at IS DISTINCT FROM OLD.logout_proof_expires_at
       OR NEW.logout_proof_digest IS DISTINCT FROM OLD.logout_proof_digest
       OR NEW.logout_proof_key_id IS DISTINCT FROM OLD.logout_proof_key_id
    THEN
       RAISE EXCEPTION 'auth_session_immutable_fields' USING ERRCODE = '23514';
    END IF;

    -- Repeated reads must not rewrite the receipt or touch revoked rows.
    IF NEW IS NOT DISTINCT FROM OLD THEN
        RETURN NEW;
    END IF;

    IF OLD.revoked_at IS NOT NULL THEN
        RAISE EXCEPTION 'auth_session_revoked_write' USING ERRCODE = '23514';
    END IF;

    -- Must be measured after the row lock, not transaction start.
    decision_clock := clock_timestamp();
    IF decision_clock >= OLD.absolute_expires_at THEN
        RAISE EXCEPTION 'auth_session_expired_write' USING ERRCODE = '23514';
    END IF;

    IF NEW.revoked_at IS NULL THEN
        -- Refresh rotation is an atomic generation + changed digest pair.
        IF NEW.last_logout_operation_digest IS DISTINCT FROM OLD.last_logout_operation_digest
           OR NEW.receipt_key_version IS DISTINCT FROM OLD.receipt_key_version
           OR OLD.refresh_generation >= 9223372036854775807
           OR NEW.refresh_generation <> OLD.refresh_generation + 1
           OR NEW.refresh_credential_digest IS NOT DISTINCT FROM OLD.refresh_credential_digest
        THEN
            RAISE EXCEPTION 'auth_session_invalid_refresh_transition' USING ERRCODE = '23514';
        END IF;
    ELSE
        -- First revocation changes the three receipt fields together, never refresh.
        IF OLD.last_logout_operation_digest IS NOT NULL
           OR OLD.receipt_key_version IS NOT NULL
           OR NEW.last_logout_operation_digest IS NULL
           OR NEW.receipt_key_version IS NULL
           OR NEW.refresh_generation IS DISTINCT FROM OLD.refresh_generation
           OR NEW.refresh_credential_digest IS DISTINCT FROM OLD.refresh_credential_digest
           OR NEW.revoked_at < OLD.created_at
           OR NEW.revoked_at > decision_clock
        THEN
            RAISE EXCEPTION 'auth_session_invalid_revocation_transition' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$fitflow$
"""


GUARD_DELETE_SQL = """
CREATE FUNCTION fitflow_auth_sessions_guard_delete_v1()
RETURNS trigger
LANGUAGE plpgsql
AS $fitflow$
BEGIN
    IF clock_timestamp() < OLD.logout_proof_expires_at THEN
        RAISE EXCEPTION 'auth_session_retention_not_elapsed' USING ERRCODE = '23514';
    END IF;
    RETURN OLD;
END;
$fitflow$
"""


def upgrade() -> None:
    """Create only the isolated, initially empty storage contract."""
    op.create_table(
        "auth_sessions",
        sa.Column("sid", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
        ),
        sa.Column("refresh_generation", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("refresh_credential_digest", postgresql.BYTEA(), nullable=False),
        sa.Column("logout_proof_digest", postgresql.BYTEA(), nullable=False),
        sa.Column("logout_proof_key_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(timezone=True), nullable=False,
            server_default=sa.text("transaction_timestamp()"),
        ),
        sa.Column("absolute_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("logout_proof_expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_logout_operation_digest", postgresql.BYTEA(), nullable=True),
        sa.Column("receipt_key_version", sa.String(length=64), nullable=True),
        sa.CheckConstraint("refresh_generation >= 0", name="ck_auth_sessions_generation"),
        sa.CheckConstraint(
            "octet_length(refresh_credential_digest) = 32", name="ck_auth_sessions_refresh_digest"
        ),
        sa.CheckConstraint(
            "octet_length(logout_proof_digest) = 32", name="ck_auth_sessions_logout_digest"
        ),
        sa.CheckConstraint(
            "length(btrim(logout_proof_key_id)) > 0", name="ck_auth_sessions_logout_kid"
        ),
        sa.CheckConstraint(
            "absolute_expires_at > created_at", name="ck_auth_sessions_absolute_expiry"
        ),
        sa.CheckConstraint(
            "logout_proof_expires_at = absolute_expires_at + INTERVAL '24 hours'",
            name="ck_auth_sessions_proof_expiry",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL AND last_logout_operation_digest IS NULL AND "
            "receipt_key_version IS NULL) OR "
            "(revoked_at IS NOT NULL AND last_logout_operation_digest IS NOT NULL AND "
            "receipt_key_version IS NOT NULL)",
            name="ck_auth_sessions_receipt_atomic",
        ),
        sa.CheckConstraint(
            "last_logout_operation_digest IS NULL OR "
            "octet_length(last_logout_operation_digest) = 32",
            name="ck_auth_sessions_receipt_digest",
        ),
        sa.CheckConstraint(
            "receipt_key_version IS NULL OR length(btrim(receipt_key_version)) > 0",
            name="ck_auth_sessions_receipt_key_version",
        ),
    )
    op.create_index(
        "ix_auth_sessions_user_created", "auth_sessions",
        ["user_id", sa.text("created_at DESC")], unique=False,
    )
    op.create_index(
        "ix_auth_sessions_proof_expires", "auth_sessions", ["logout_proof_expires_at"],
        unique=False,
    )
    op.execute(GUARD_INSERT_SQL)
    op.execute(GUARD_UPDATE_SQL)
    op.execute(GUARD_DELETE_SQL)
    op.execute(
        "CREATE TRIGGER fitflow_auth_sessions_before_insert_v1 "
        "BEFORE INSERT ON auth_sessions FOR EACH ROW "
        "EXECUTE FUNCTION fitflow_auth_sessions_guard_insert_v1()"
    )
    op.execute(
        "CREATE TRIGGER fitflow_auth_sessions_before_update_v1 "
        "BEFORE UPDATE ON auth_sessions FOR EACH ROW "
        "EXECUTE FUNCTION fitflow_auth_sessions_guard_update_v1()"
    )
    op.execute(
        "CREATE TRIGGER fitflow_auth_sessions_before_delete_v1 "
        "BEFORE DELETE ON auth_sessions FOR EACH ROW "
        "EXECUTE FUNCTION fitflow_auth_sessions_guard_delete_v1()"
    )


def downgrade() -> None:
    """Downgrading durable revocation evidence is explicitly prohibited."""
    raise RuntimeError("auth_sessions is forward-only; authorize a separate migration")

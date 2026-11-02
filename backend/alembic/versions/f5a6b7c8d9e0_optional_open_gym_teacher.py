"""Allow teacherless class schedules for open-gym application semantics.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
"""

from collections.abc import Sequence

from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f5a6b7c8d9e0"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Permit NULL teacher_id; activity-sensitive rules remain in the app."""
    op.alter_column(
        "class_schedules",
        "teacher_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    """Restore the historical database-level Teacher requirement."""
    op.alter_column(
        "class_schedules",
        "teacher_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

"""Add soft-delete timestamp for class sessions.

Revision ID: b1a2c3d4e5f6
Revises: 9c3e4f506172
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b1a2c3d4e5f6"
down_revision: str | None = "9c3e4f506172"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persist the timestamp required by ClassSession soft deletion."""
    op.add_column(
        "class_sessions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove only the timestamp introduced by this revision."""
    op.drop_column("class_sessions", "deleted_at")

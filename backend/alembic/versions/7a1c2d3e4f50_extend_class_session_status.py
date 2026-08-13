"""Extend ClassSessionStatus with open and closed.

Revision ID: 7a1c2d3e4f50
Revises: 38d9796100f0
"""

from collections.abc import Sequence

from alembic import op

revision: str = "7a1c2d3e4f50"
down_revision: str | None = "38d9796100f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the operational states accepted by the active domain contract."""
    op.execute("ALTER TYPE classsessionstatus ADD VALUE IF NOT EXISTS 'open'")
    op.execute("ALTER TYPE classsessionstatus ADD VALUE IF NOT EXISTS 'closed'")


def downgrade() -> None:
    """Enum value removal requires a data-aware replacement migration."""
    raise NotImplementedError("This forward-only enum migration cannot be downgraded safely")

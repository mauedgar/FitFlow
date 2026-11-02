"""Add gym_only to allowedplan.

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-08-13
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "b1a2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the schedule-level gym-only restriction without recreating data."""
    op.execute("ALTER TYPE allowedplan ADD VALUE IF NOT EXISTS 'gym_only'")


def downgrade() -> None:
    """Prevent a destructive rollback of a PostgreSQL enum value."""
    raise NotImplementedError(
        "Removing a PostgreSQL enum value requires a separately approved "
        "data-preserving migration."
    )

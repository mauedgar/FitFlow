"""Add minimal actor audit columns to class schedules.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable actor references without changing existing cascades."""
    op.add_column(
        "class_schedules",
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "class_schedules",
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_class_schedules_created_by_id_users",
        "class_schedules",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_class_schedules_updated_by_id_users",
        "class_schedules",
        "users",
        ["updated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove only the actor-audit additions from this revision."""
    op.drop_constraint("fk_class_schedules_updated_by_id_users", "class_schedules", type_="foreignkey")
    op.drop_constraint("fk_class_schedules_created_by_id_users", "class_schedules", type_="foreignkey")
    op.drop_column("class_schedules", "updated_by_id")
    op.drop_column("class_schedules", "created_by_id")

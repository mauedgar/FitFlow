"""Add missing schedule and gym class integrity constraints.

Revision ID: 9c3e4f506172
Revises: 8b2d3e4f5061
"""

from collections.abc import Sequence

from alembic import op

revision: str = "9c3e4f506172"
down_revision: str | None = "8b2d3e4f5061"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enforce the positive values already required by API contracts."""
    op.create_check_constraint(
        "ck_class_schedule_capacity_positive",
        "class_schedules",
        "capacity >= 1",
    )
    op.create_check_constraint(
        "ck_class_schedule_duration_positive",
        "class_schedules",
        "duration_minutes >= 1",
    )
    op.create_index(
        "ix_class_schedule_teacher_id",
        "class_schedules",
        ["teacher_id"],
    )
    op.create_index(
        "ix_class_schedule_gym_class_id",
        "class_schedules",
        ["gym_class_id"],
    )
    op.create_index(
        "ix_class_schedule_start_date_time",
        "class_schedules",
        ["start_date", "start_time"],
    )
    op.create_check_constraint(
        "ck_gym_class_duration_positive",
        "gym_classes",
        "duration_minutes >= 1",
    )
    op.create_check_constraint(
        "ck_gym_class_capacity_positive",
        "gym_classes",
        "default_capacity >= 1",
    )


def downgrade() -> None:
    """Remove only the constraints and indexes introduced here."""
    op.drop_constraint(
        "ck_gym_class_capacity_positive", "gym_classes", type_="check"
    )
    op.drop_constraint(
        "ck_gym_class_duration_positive", "gym_classes", type_="check"
    )
    op.drop_index("ix_class_schedule_start_date_time", table_name="class_schedules")
    op.drop_index("ix_class_schedule_gym_class_id", table_name="class_schedules")
    op.drop_index("ix_class_schedule_teacher_id", table_name="class_schedules")
    op.drop_constraint(
        "ck_class_schedule_duration_positive", "class_schedules", type_="check"
    )
    op.drop_constraint(
        "ck_class_schedule_capacity_positive", "class_schedules", type_="check"
    )

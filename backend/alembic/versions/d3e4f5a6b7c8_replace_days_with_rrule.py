"""Replace days_of_week with canonical RRULE recurrence.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill legacy weekdays, then remove the parallel recurrence source."""
    op.add_column("class_schedules", sa.Column("rrule", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE class_schedules
        SET rrule = 'RRULE:FREQ=WEEKLY;BYDAY=' || (
            SELECT string_agg(
                CASE value::int
                    WHEN 0 THEN 'MO' WHEN 1 THEN 'TU' WHEN 2 THEN 'WE'
                    WHEN 3 THEN 'TH' WHEN 4 THEN 'FR' WHEN 5 THEN 'SA'
                    WHEN 6 THEN 'SU'
                END,
                ',' ORDER BY value::int
            )
            FROM jsonb_array_elements_text(days_of_week)
        )
        """
    )
    missing = op.get_bind().execute(
        sa.text("SELECT count(*) FROM class_schedules WHERE rrule IS NULL")
    ).scalar_one()
    if missing:
        raise RuntimeError("No se pudo convertir days_of_week a RRULE para todos los schedules.")
    op.alter_column("class_schedules", "rrule", nullable=False)
    op.drop_column("class_schedules", "days_of_week")


def downgrade() -> None:
    """Prevent a lossy rollback to a parallel recurrence representation."""
    raise NotImplementedError("La recurrencia RRULE no se revierte a days_of_week.")

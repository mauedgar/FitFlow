"""Allow re-booking after cancellation while preserving history.

Revision ID: 8b2d3e4f5061
Revises: 7a1c2d3e4f50
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "8b2d3e4f5061"
down_revision: str | None = "7a1c2d3e4f50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace absolute uniqueness with uniqueness for non-cancelled bookings."""
    op.drop_constraint("uq_booking_client_session", "bookings", type_="unique")
    op.create_index(
        "uq_booking_active_client_session",
        "bookings",
        ["client_id", "class_session_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'cancelled'::bookingstatus"),
    )


def downgrade() -> None:
    """Restore absolute uniqueness if no historical duplicates exist."""
    op.drop_index("uq_booking_active_client_session", table_name="bookings")
    op.create_unique_constraint(
        "uq_booking_client_session",
        "bookings",
        ["client_id", "class_session_id"],
    )

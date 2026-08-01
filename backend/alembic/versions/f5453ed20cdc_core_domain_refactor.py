"""Core domain refactor

Revision ID: f5453ed20cdc
Revises: a2b62b427037
Create Date: 2026-08-01 00:11:31.452452
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f5453ed20cdc"
down_revision: Union[str, Sequence[str], None] = "a2b62b427037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
#  ENUM definitions (LOWERCASE, one place only)
# ---------------------------------------------------------------------------
allowed_plan_enum = postgresql.ENUM(
    "classes", "premium", "personalized", name="allowedplan_enum"
)
activity_type_enum = postgresql.ENUM(
    "group_class", "open_gym", "personal_training", name="activitytype_enum"
)
class_session_status_enum = postgresql.ENUM(
    "scheduled", "cancelled", "completed", name="classsessionstatus_enum"
)
membership_status_enum = postgresql.ENUM(
    "active", "expired", "paused", "cancelled", name="membershipstatus_enum"
)
difficulty_level_enum_new = postgresql.ENUM(
    "beginner", "intermediate", "advanced", name="difficultylevel_enum_new"
)  # temporal mientras dropeamos la vieja


# ===========================================================================
# UPGRADE
# ===========================================================================
def upgrade() -> None:
    bind = op.get_bind()

    # 1. Crear nuevos ENUMS --------------------------------------------------
    for enum_type in (
        allowed_plan_enum,
        activity_type_enum,
        class_session_status_enum,
        membership_status_enum,
        difficulty_level_enum_new,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    # 2. DROP entidades obsoletas (sin datos que salvar) ---------------------
    op.drop_table("teacher_class_association")
    # 2️⃣  TRUNCATE DE TODAS LAS TABLAS CON CAMBIOS NOT NULL -------------
    #    Ajusta la lista si tienes más/menos tablas.  CASCADE elimina en
    #    cascada los registros relacionados para no violar FKs.
    op.execute(
        """
        TRUNCATE TABLE
            bookings,
            class_sessions,
            class_schedules,
            gym_classes,
            memberships,
            clients,
            teachers,
            persons
        CASCADE
        """
    )
    # 3. BOOKINGS ------------------------------------------------------------
    op.add_column(
        "bookings", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "bookings", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "bookings",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("bookings", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.create_unique_constraint("uq_booking_client_session", "bookings", ["client_id", "class_session_id"])
    op.drop_column("bookings", "booking_date")

    # 4. CLASS_SCHEDULES -----------------------------------------------------
    op.add_column("class_schedules", sa.Column("duration_minutes", sa.Integer(), nullable=False))
    op.add_column("class_schedules", sa.Column("capacity", sa.Integer(), nullable=False))
    op.add_column("class_schedules", sa.Column("allowed_plan", allowed_plan_enum, nullable=True))
    op.add_column(
        "class_schedules",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "class_schedules",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("class_schedules", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("class_schedules", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column(
        "class_schedules",
        "start_time",
        existing_type=postgresql.TIME(timezone=True),
        type_=sa.Time(),
        existing_nullable=False,
    )
    op.drop_column("class_schedules", "max_capacity")
    op.drop_column("class_schedules", "end_time")

    # 5. CLASS_SESSIONS ------------------------------------------------------
    op.add_column("class_sessions", sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False))
    op.add_column("class_sessions", sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False))
    op.add_column("class_sessions", sa.Column("capacity_snapshot", sa.Integer(), nullable=False))
    op.add_column("class_sessions", sa.Column("status", class_session_status_enum, nullable=False))
    op.add_column(
        "class_sessions",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "class_sessions",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("class_sessions", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.drop_constraint(op.f("_class_schedule_datetime_uc"), "class_sessions", type_="unique")
    op.drop_index(op.f("ix_class_sessions_start_datetime"), table_name="class_sessions")
    op.create_index(op.f("ix_class_sessions_starts_at"), "class_sessions", ["starts_at"], unique=False)
    op.create_unique_constraint("uq_class_schedule_starts_at", "class_sessions", ["class_schedule_id", "starts_at"])
    op.drop_column("class_sessions", "end_datetime")
    op.drop_column("class_sessions", "start_datetime")
    op.drop_column("class_sessions", "is_cancelled")

    # 6. GYM_CLASSES ---------------------------------------------------------
    op.add_column("gym_classes", sa.Column("activity_type", activity_type_enum, nullable=False))
    op.add_column("gym_classes", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column(
        "gym_classes",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "gym_classes",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("gym_classes", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("gym_classes", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    #   Replace old difficulty enum with new one (simplest: drop + recreate column)
    op.drop_column("gym_classes", "difficulty")
    op.add_column("gym_classes", sa.Column("difficulty", difficulty_level_enum_new, nullable=True))

    # 7. MEMBERSHIPS ---------------------------------------------------------
    op.add_column("memberships", sa.Column("status", membership_status_enum, nullable=False))
    op.add_column(
        "memberships",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "memberships",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("memberships", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("memberships", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # 8. PERSONS -------------------------------------------------------------
    op.add_column("persons", sa.Column("first_name", sa.String(), nullable=False))
    op.add_column("persons", sa.Column("last_name", sa.String(), nullable=False))
    op.add_column("persons", sa.Column("document_number", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("profile_image_url", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("person_type", sa.String(length=50), nullable=True))
    op.add_column(
        "persons",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "persons",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("persons", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("persons", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_index(op.f("ix_persons_name"), table_name="persons")
    op.drop_index(op.f("ix_persons_passport"), table_name="persons")
    op.drop_index(op.f("ix_persons_surname"), table_name="persons")
    op.create_index(op.f("ix_persons_document_number"), "persons", ["document_number"], unique=True)
    op.create_index(op.f("ix_persons_first_name"), "persons", ["first_name"], unique=False)
    op.create_index(op.f("ix_persons_last_name"), "persons", ["last_name"], unique=False)
    op.drop_column("persons", "type")
    op.drop_column("persons", "profile_img_url")
    op.drop_column("persons", "name")
    op.drop_column("persons", "surname")
    op.drop_column("persons", "passport")

    # 9. USERS ---------------------------------------------------------------
    op.add_column("users", sa.Column("active", sa.Boolean(), server_default="true", nullable=False))
    # convert TIMESTAMP WITHOUT TIME ZONE to timestamptz if you wish, but we keep autogen changes
    op.alter_column(
        "users",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "users",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "users",
        "deleted_at",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.drop_column("users", "is_active")

    # 10. Clean up old ENUM types -------------------------------------------
    op.execute("DROP TYPE IF EXISTS allowedplan")
    op.execute("DROP TYPE IF EXISTS activitytype")
    op.execute("DROP TYPE IF EXISTS classsessionstatus")
    op.execute("DROP TYPE IF EXISTS membershipstatus")
    op.execute("DROP TYPE IF EXISTS difficultylevel")
    # ### end upgrade ###


# ===========================================================================
# DOWNGRADE (reverse the order)
# ===========================================================================
def downgrade() -> None:
    # 1. Re-create old ENUMs --------------------------------------------------
    old_allowed = postgresql.ENUM("BASIC", "PREMIUM", "PERSONALIZED", name="allowedplan")
    old_activity = postgresql.ENUM("GROUP_CLASS", "OPEN_GYM", "PERSONAL_TRAINING", name="activitytype")
    old_session_status = postgresql.ENUM("SCHEDULED", "CANCELLED", "COMPLETED", name="classsessionstatus")
    old_membership_status = postgresql.ENUM("ACTIVE", "EXPIRED", "PAUSED", "CANCELLED", name="membershipstatus")
    old_difficulty = postgresql.ENUM("BEGINNER", "INTERMEDIATE", "ADVANCED", name="difficultylevel")

    for enum_type in (old_allowed, old_activity, old_session_status, old_membership_status, old_difficulty):
        enum_type.create(op.get_bind(), checkfirst=True)

    # 2. USERS ---------------------------------------------------------------
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.drop_column("users", "active")
    op.alter_column("users", "deleted_at", type_=postgresql.TIMESTAMP(), existing_type=sa.DateTime(timezone=True))
    op.alter_column("users", "updated_at", type_=postgresql.TIMESTAMP(), existing_type=sa.DateTime(timezone=True))
    op.alter_column("users", "created_at", type_=postgresql.TIMESTAMP(), existing_type=sa.DateTime(timezone=True))

    # 3. PERSONS -------------------------------------------------------------
    op.add_column("persons", sa.Column("passport", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("surname", sa.String(), nullable=False))
    op.add_column("persons", sa.Column("name", sa.String(), nullable=False))
    op.add_column("persons", sa.Column("profile_img_url", sa.String(), nullable=True))
    op.add_column("persons", sa.Column("type", sa.String(length=50), nullable=True))
    op.drop_index(op.f("ix_persons_last_name"), table_name="persons")
    op.drop_index(op.f("ix_persons_first_name"), table_name="persons")
    op.drop_index(op.f("ix_persons_document_number"), table_name="persons")
    op.create_index(op.f("ix_persons_surname"), "persons", ["surname"], unique=False)
    op.create_index(op.f("ix_persons_passport"), "persons", ["passport"], unique=True)
    op.create_index(op.f("ix_persons_name"), "persons", ["name"], unique=False)
    op.drop_column("persons", "deleted_at")
    op.drop_column("persons", "active")
    op.drop_column("persons", "updated_at")
    op.drop_column("persons", "created_at")
    op.drop_column("persons", "person_type")
    op.drop_column("persons", "profile_image_url")
    op.drop_column("persons", "document_number")
    op.drop_column("persons", "last_name")
    op.drop_column("persons", "first_name")

    # 4. MEMBERSHIPS ---------------------------------------------------------
    op.drop_column("memberships", "deleted_at")
    op.drop_column("memberships", "active")
    op.drop_column("memberships", "updated_at")
    op.drop_column("memberships", "created_at")
    op.drop_column("memberships", "status")

    # 5. GYM_CLASSES ---------------------------------------------------------
    op.drop_column("gym_classes", "deleted_at")
    op.drop_column("gym_classes", "active")
    op.drop_column("gym_classes", "updated_at")
    op.drop_column("gym_classes", "created_at")
    op.drop_column("gym_classes", "image_url")
    op.drop_column("gym_classes", "activity_type")
    op.drop_column("gym_classes", "difficulty")

    op.add_column(
        "gym_classes",
        sa.Column("difficulty", old_difficulty, nullable=True),
    )

    # 6. CLASS_SESSIONS ------------------------------------------------------
    op.add_column("class_sessions", sa.Column("is_cancelled", sa.Boolean(), nullable=False))
    op.add_column("class_sessions", sa.Column("start_datetime", postgresql.TIMESTAMP(timezone=True), nullable=False))
    op.add_column("class_sessions", sa.Column("end_datetime", postgresql.TIMESTAMP(timezone=True), nullable=False))
    op.drop_constraint("uq_class_schedule_starts_at", "class_sessions", type_="unique")
    op.drop_index(op.f("ix_class_sessions_starts_at"), table_name="class_sessions")
    op.create_index(op.f("ix_class_sessions_start_datetime"), "class_sessions", ["start_datetime"])
    op.create_unique_constraint(
        op.f("_class_schedule_datetime_uc"), "class_sessions", ["class_schedule_id", "start_datetime"]
    )
    op.drop_column("class_sessions", "active")
    op.drop_column("class_sessions", "updated_at")
    op.drop_column("class_sessions", "created_at")
    op.drop_column("class_sessions", "status")
    op.drop_column("class_sessions", "capacity_snapshot")
    op.drop_column("class_sessions", "ends_at")
    op.drop_column("class_sessions", "starts_at")

    # 7. CLASS_SCHEDULES -----------------------------------------------------
    op.add_column("class_schedules", sa.Column("end_time", postgresql.TIME(timezone=True), nullable=False))
    op.add_column("class_schedules", sa.Column("max_capacity", sa.Integer(), nullable=False))
    op.alter_column(
        "class_schedules",
        "start_time",
        type_=postgresql.TIME(timezone=True),
        existing_type=sa.Time(),
    )
    op.drop_column("class_schedules", "deleted_at")
    op.drop_column("class_schedules", "active")
    op.drop_column("class_schedules", "updated_at")
    op.drop_column("class_schedules", "created_at")
    op.drop_column("class_schedules", "allowed_plan")
    op.drop_column("class_schedules", "capacity")
    op.drop_column("class_schedules", "duration_minutes")

    # 8. BOOKINGS ------------------------------------------------------------
    op.add_column("bookings", sa.Column("booking_date", postgresql.TIMESTAMP(timezone=True), nullable=False))
    op.drop_constraint("uq_booking_client_session", "bookings", type_="unique")
    op.drop_column("bookings", "active")
    op.drop_column("bookings", "updated_at")
    op.drop_column("bookings", "created_at")
    op.drop_column("bookings", "cancelled_at")
    op.drop_column("bookings", "checked_in_at")

    # 9. Re-create teacher_class_association ---------------------------------
    op.create_table(
        "teacher_class_association",
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("gym_class_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gym_class_id"], ["gym_classes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("teacher_id", "gym_class_id"),
    )

    # 10. Drop new enums -----------------------------------------------------
    for enum_type in (
        allowed_plan_enum,
        activity_type_enum,
        class_session_status_enum,
        membership_status_enum,
        difficulty_level_enum_new,
    ):
        enum_type.drop(op.get_bind(), checkfirst=True)
    # ### end downgrade ###
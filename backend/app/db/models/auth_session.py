"""Persistent, per-login session metadata (G2-A1: storage only).

No authentication route reads this model until the separately authorized A2.
The database migration owns write-once and cleanup protections.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    sid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    refresh_generation: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    refresh_credential_digest: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    logout_proof_digest: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    logout_proof_key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("transaction_timestamp()")
    )
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    logout_proof_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_logout_operation_digest: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    receipt_key_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        CheckConstraint("refresh_generation >= 0", name="ck_auth_sessions_generation"),
        CheckConstraint(
            "octet_length(refresh_credential_digest) = 32", name="ck_auth_sessions_refresh_digest"
        ),
        CheckConstraint(
            "octet_length(logout_proof_digest) = 32", name="ck_auth_sessions_logout_digest"
        ),
        CheckConstraint(
            "length(btrim(logout_proof_key_id)) > 0", name="ck_auth_sessions_logout_kid"
        ),
        CheckConstraint(
            "absolute_expires_at > created_at", name="ck_auth_sessions_absolute_expiry"
        ),
        CheckConstraint(
            "logout_proof_expires_at = absolute_expires_at + INTERVAL '24 hours'",
            name="ck_auth_sessions_proof_expiry",
        ),
        CheckConstraint(
            "(revoked_at IS NULL AND last_logout_operation_digest IS NULL AND "
            "receipt_key_version IS NULL) OR "
            "(revoked_at IS NOT NULL AND last_logout_operation_digest IS NOT NULL AND "
            "receipt_key_version IS NOT NULL)",
            name="ck_auth_sessions_receipt_atomic",
        ),
        CheckConstraint(
            "last_logout_operation_digest IS NULL OR "
            "octet_length(last_logout_operation_digest) = 32",
            name="ck_auth_sessions_receipt_digest",
        ),
        CheckConstraint(
            "receipt_key_version IS NULL OR length(btrim(receipt_key_version)) > 0",
            name="ck_auth_sessions_receipt_key_version",
        ),
        Index("ix_auth_sessions_user_created", "user_id", text("created_at DESC")),
        Index("ix_auth_sessions_proof_expires", "logout_proof_expires_at"),
    )

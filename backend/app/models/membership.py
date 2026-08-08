"""Modelo ORM de las membresías de FitFlow."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MembershipPlan, MembershipStatus
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client


class Membership(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Membresía asociada a un cliente.

    Esta entidad define el tipo de acceso comercial del cliente,
    su vigencia temporal y algunos metadatos operativos útiles
    para control de ingreso y futura facturación.
    """

    __tablename__ = "memberships"

    # Identificador único de la membresía.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Plan comercial contratado por el cliente.
    plan: Mapped[MembershipPlan] = mapped_column(
        SQLAlchemyEnum(
            MembershipPlan,
            name="membershipplan",
        ),
        nullable=False,
        default=MembershipPlan.gym_only,
    )

    # Estado operativo de la membresía.
    status: Mapped[MembershipStatus] = mapped_column(
        SQLAlchemyEnum(
            MembershipStatus,
            name="membershipstatus",
        ),
        nullable=False,
        default=MembershipStatus.active,
    )

    # Fecha de inicio de vigencia.
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Fecha de finalización de vigencia.
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Último check-in registrado para esta membresía.
    last_check_in: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Referencia opcional a la última factura o comprobante externo.
    last_invoice_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # Cliente titular de la membresía.
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        unique=True,
        nullable=False,
    )

    # Relación inversa con el cliente.
    client: Mapped[Client] = relationship(
        "Client",
        back_populates="membership",
    )


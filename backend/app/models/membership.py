import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin
from backend.app.core.enums import MembershipPlan, MembershipStatus

if TYPE_CHECKING:
    from .client import Client


class Membership(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Membresía asociada a un cliente.

    Esta entidad define el tipo de acceso comercial del cliente,
    su vigencia temporal y algunos metadatos operativos útiles
    para control de ingreso y futura facturación.
    """

    __tablename__ = "memberships" # pyright: ignore[reportAssignmentType]

    # Identificador único de la membresía.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan comercial contratado por el cliente.
    plan = Column(
        SQLAlchemyEnum(MembershipPlan, name="membershipplan"),
        nullable=False,
        default=MembershipPlan.gym_only,
    )

    # Estado operativo de la membresía.
    status = Column(
        SQLAlchemyEnum(MembershipStatus, name="membershipstatus"),
        nullable=False,
        default=MembershipStatus.active,
    )

    # Fecha de inicio de vigencia.
    start_date = Column(DateTime(timezone=True), nullable=False)

    # Fecha de finalización de vigencia.
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Último check-in registrado para esta membresía.
    last_check_in = Column(DateTime(timezone=True), nullable=True)

    # Referencia opcional a la última factura o comprobante externo.
    last_invoice_id = Column(String, nullable=True)

    # Cliente titular de la membresía.
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id"),
        unique=True,
        nullable=False,
    )

    # Relación inversa con el cliente.
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="membership",
    )

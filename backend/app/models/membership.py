import uuid
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, String, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, ActiveMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .client import Client


class MembershipPlan(str, enum.Enum):
    """
    Tipos de membresía que ofrece el gimnasio.

    - gym_only: acceso a musculación o gimnasio libre.
    - classes: acceso a clases grupales.
    - premium: acceso combinado a musculación y clases.
    - personalized: acceso premium más atención o entrenamiento personalizado.
    """
    GYM_ONLY = "gym_only"
    CLASSES = "classes"
    PREMIUM = "premium"
    PERSONALIZED = "personalized"


class MembershipStatus(str, enum.Enum):
    """
    Estados operativos posibles de una membresía.

    - active: la membresía está vigente y habilitada.
    - expired: la vigencia terminó.
    - paused: la membresía está temporalmente suspendida.
    - cancelled: la membresía fue dada de baja.
    """
    ACTIVE = "active"
    EXPIRED = "expired"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Membership(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """
    Membresía asociada a un cliente.

    Esta entidad define el tipo de acceso comercial del cliente,
    su vigencia temporal y algunos metadatos operativos útiles
    para control de ingreso y futura facturación.
    """
    __tablename__ = "memberships"

    # Identificador único de la membresía.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan comercial contratado por el cliente.
    plan = Column(
        SQLAlchemyEnum(MembershipPlan, name="membershipplan"),
        nullable=False,
        default=MembershipPlan.GYM_ONLY
    )

    # Estado operativo de la membresía.
    status = Column(
        SQLAlchemyEnum(MembershipStatus, name="membershipstatus"),
        nullable=False,
        default=MembershipStatus.ACTIVE
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
        nullable=False
    )

    # Relación inversa con el cliente.
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="membership"
    )
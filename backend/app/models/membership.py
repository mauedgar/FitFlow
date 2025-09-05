import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Usamos un Enum para los tipos de planes. Esto es muy escalable.
class MembershipPlan(str, enum.Enum):
    BASIC = "basic"         # Ej: Acceso al gimnasio
    PLUS = "plus"           # Ej: Acceso + clases grupales
    PREMIUM = "premium"     # Ej: Acceso total + entrenador personal

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # El tipo de plan que tiene el cliente
    plan = Column(SQLAlchemyEnum(MembershipPlan), nullable=False, default=MembershipPlan.BASIC)
    
    # Fechas clave para la gestión de la suscripción
    start_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False) # Se calculará al crear/renovar
    
    # Para la lógica de control de ingreso
    last_check_in = Column(DateTime(timezone=True), nullable=True)
    
    # Relación con la facturación (billing)
    # Suponemos que tendrás un microservicio o tabla de 'invoices' en el futuro.
    # Por ahora, puede ser un simple string.
    last_invoice_id = Column(String, nullable=True) 

    # --- Relación Inversa con Client ---
    # Una membresía pertenece a un único cliente.
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), unique=True, nullable=False)
    client = relationship("Client", back_populates="membership")

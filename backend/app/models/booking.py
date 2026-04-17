# app/models/booking.py (Crea este nuevo archivo)
import uuid
import enum
from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .client import Client
    from .class_session import ClassSession

class BookingStatus(str, enum.Enum):
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'
    PENDING = 'PENDING' 

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    
    # ⭐ La reserva es para una sesión de clase específica
    class_session_id = Column(UUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False)
    
    booking_date = Column(DateTime(timezone=True), nullable=False) 
    status = Column(SQLAlchemyEnum(BookingStatus, name= 'bookingstatus'), nullable=False, default=BookingStatus.CONFIRMED.value)

    # Relaciones
    client: Mapped["Client"] = relationship(back_populates="bookings") 
    class_session: Mapped["ClassSession"] = relationship(back_populates="bookings")
    
    # Opcional: Asegurar que un cliente solo reserve una sesión una vez
    # from sqlalchemy import UniqueConstraint
    # __table_args__ = (UniqueConstraint('client_id', 'class_session_id', name='_client_session_uc'),)
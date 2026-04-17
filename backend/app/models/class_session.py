# app/models/class_session.py (Crea este nuevo archivo)
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
from typing import List # 👈 AÑADE ESTO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .booking import Booking 
    from .class_schedule import ClassSchedule
class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ⭐ Vincula a la oferta recurrente de la que forma parte
    class_schedule_id = Column(UUID(as_uuid=True), ForeignKey("class_schedules.id", ondelete="CASCADE"), nullable=False)
    
    # ⭐ Fecha y hora exactas de ESTA ocurrencia específica
    start_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime = Column(DateTime(timezone=True), nullable=False) 
    
    is_cancelled = Column(Boolean, default=False, nullable=False) # Para cancelar sesiones individuales
    
    # Relaciones
    class_schedule: Mapped["ClassSchedule"] = relationship(back_populates="sessions")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="class_session")
    
    # Opcional: Para asegurar que no haya dos sesiones iguales para el mismo horario y fecha/hora
    from sqlalchemy import UniqueConstraint
    __table_args__ = (UniqueConstraint('class_schedule_id', 'start_datetime', name='_class_schedule_datetime_uc'),)
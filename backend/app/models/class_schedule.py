# app/models/class_schedule.py (Crea este nuevo archivo)
import uuid
from sqlalchemy import Column, Integer, Time, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID, JSONB # JSONB para almacenar arrays de días de la semana
from app.db.base_class import Base
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .gym_class import GymClass
    from .class_session import ClassSession
    from .teacher import Teacher
class ClassSchedule(Base):
    __tablename__ = "class_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ⭐ Qué clase es (ej. Yoga Avanzado)
    gym_class_id = Column(UUID(as_uuid=True), ForeignKey("gym_classes.id", ondelete="CASCADE"), nullable=False)
    
    # ⭐ Quién la imparte
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    
    # ⭐ Días de la semana (ej. [0, 2] para Lunes y Miércoles, donde 0=Lunes, 1=Martes, etc.)
    days_of_week = Column(JSONB, nullable=False) # Guardará un array de ints, ej: [0, 2]
    
    # ⭐ Hora de inicio y fin para esta oferta recurrente
    start_time = Column(Time(timezone=True), nullable=False) 
    end_time = Column(Time(timezone=True), nullable=False) 
    
    # ⭐ Capacidad máxima para CADA SESIÓN de esta oferta recurrente
    max_capacity = Column(Integer, nullable=False, default=10) # Puede usar GymClass.default_capacity como base
    
    # ⭐ Rango de fechas para esta oferta (opcional, útil para temporadas o fin de cursos)
    start_date = Column(Date, nullable=False) 
    end_date = Column(Date, nullable=True) # Si es null, la oferta es indefinida

    # Relaciones
    gym_class: Mapped["GymClass"] = relationship("GymClass", back_populates="class_schedules")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="class_schedules")
    
    # Relación con las sesiones específicas que se derivan de este horario
    sessions: Mapped[List["ClassSession"]] = relationship("ClassSession", back_populates="class_schedule", cascade="all, delete-orphan")
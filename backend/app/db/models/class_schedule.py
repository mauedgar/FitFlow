# app/models/class_schedule.py
"""Modelo ClassSchedule (RRULE first, days_of_week deprecated fallback).

Representa la configuración recurrente de una clase dentro de la agenda.
- La `capacity` es la fuente de verdad y se copia a cada ClassSession generado.
- `rrule` (RFC5545) es la forma preferente de definir recurrencia.
- `days_of_week` se mantiene como fallback para compatibilidad, pero se considera
  **deprecado** cuando `rrule` está presente.
- Fechas/horas se almacenan en UTC/naive y se interpretan con LOCAL_TZ en servicios/serializers.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, relationship

from app.core.enums import AllowedPlan
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.class_session import ClassSession
    from backend.app.db.models.gym_class import GymClass
    from backend.app.db.models.teacher import Teacher


class ClassSchedule(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Configuración recurrente de una clase dentro de la agenda del gimnasio.

    Reglas y notas:
    - `capacity` debe ser >= 0.
    - `rrule` si está presente define la recurrencia; `days_of_week` se usa solo
      como fallback para compatibilidad con datos antiguos.
    - `start_date`/`end_date` definen la ventana de vigencia del schedule.
    - `start_time` define la hora del día (sin tz en DB); los servicios aplican LOCAL_TZ.
    """

    __tablename__ = "class_schedules"  # pyright: ignore[reportAssignmentType]

    # Identificador
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relaciones principales
    gym_class_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("gym_classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    teacher_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Recurrencia preferente: RRULE (RFC5545). Texto libre; parseable por dateutil.rrule.
    rrule = Column(String(length=1024), nullable=True)

    # Fallback legacy: lista de ints 0..6 representando días de la semana.
    # Mantener solo para compatibilidad; preferir rrule.
    days_of_week = Column(JSONB, nullable=True)

    # Hora de inicio (sin zona en DB; interpretar con LOCAL_TZ en servicios)
    start_time = Column(Time(timezone=False), nullable=False)

    # Duración en minutos
    duration_minutes = Column(Integer, nullable=False)

    # Capacidad por sesión (fuente de verdad)
    capacity = Column(Integer, nullable=False, default=10)

    # Ventana de vigencia del schedule
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Restricción por plan de membresía
    allowed_plan = Column(
        SQLAlchemyEnum(AllowedPlan, name="allowedplan"),
        nullable=True,
    )

    # Auditoría ligera (referencias a users, opcional)
    created_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relaciones ORM
    gym_class: Mapped["GymClass"] = relationship(  # noqa: UP037
        "GymClass",
        back_populates="class_schedules",
    )

    teacher: Mapped["Teacher"] = relationship(  # noqa: UP037
        "Teacher",
        back_populates="class_schedules",
    )

    class_sessions: Mapped[list["ClassSession"]] = relationship(  # noqa: UP037
        "ClassSession",
        back_populates="class_schedule",
        cascade="all, delete-orphan",
    )

    # Constraints / Indexes
    __table_args__ = (
        CheckConstraint("capacity >= 0", name="ck_class_schedule_capacity_non_negative"),
        Index("ix_class_schedule_teacher_id", "teacher_id"),
        Index("ix_class_schedule_gym_class_id", "gym_class_id"),
        Index("ix_class_schedule_start_date_time", "start_date", "start_time"),
    )

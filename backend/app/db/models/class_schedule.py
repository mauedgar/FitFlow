# app/models/class_schedule.py
"""Modelo vigente de ClassSchedule basado en ``days_of_week``.

Representa la configuración recurrente de una clase dentro de la agenda.
- La `capacity` es la fuente de verdad y se copia a cada ClassSession generado.
- RRULE es la arquitectura objetivo, pero requiere una migración funcional separada.
- Fechas/horas se almacenan en UTC/naive y se interpretan con LOCAL_TZ en servicios/serializers.
"""

from __future__ import annotations

import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    Integer,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AllowedPlan
from app.db.base_class import Base
from app.db.mixins import ActiveMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.class_session import ClassSession
    from app.db.models.gym_class import GymClass
    from app.db.models.teacher import Teacher


class ClassSchedule(Base, TimestampMixin, ActiveMixin, SoftDeleteMixin):
    """Configuración recurrente de una clase dentro de la agenda del gimnasio.

    Reglas y notas:
    - `capacity` debe ser >= 1.
    - `days_of_week` conserva el contrato ejecutable hasta migrar a RRULE.
    - `start_date`/`end_date` definen la ventana de vigencia del schedule.
    - `start_time` define la hora del día (sin tz en DB); los servicios aplican LOCAL_TZ.
    """

    __tablename__ = "class_schedules"

    # Identificador
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Relaciones principales
    gym_class_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("gym_classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Representación vigente. RRULE se incorporará en su migración funcional.
    days_of_week: Mapped[list[int]] = mapped_column(JSONB, nullable=False)

    # Hora de inicio (sin zona en DB; interpretar con LOCAL_TZ en servicios)
    start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)

    # Duración en minutos
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Capacidad por sesión (fuente de verdad)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Ventana de vigencia del schedule
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Restricción por plan de membresía
    allowed_plan: Mapped[AllowedPlan | None] = mapped_column(
        SQLAlchemyEnum(AllowedPlan, name="allowedplan"),
        nullable=True,
    )

    # Relaciones ORM
    gym_class: Mapped["GymClass"] = relationship(  # noqa: UP037
        "GymClass",
        back_populates="class_schedules",
        lazy="raise",
    )

    teacher: Mapped["Teacher"] = relationship(  # noqa: UP037
        "Teacher",
        back_populates="class_schedules",
        lazy="raise",
    )

    class_sessions: Mapped[list["ClassSession"]] = relationship(  # noqa: UP037
        "ClassSession",
        back_populates="class_schedule",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    # Constraints / Indexes
    __table_args__ = (
        CheckConstraint("capacity >= 1", name="ck_class_schedule_capacity_positive"),
        CheckConstraint(
            "duration_minutes >= 1",
            name="ck_class_schedule_duration_positive",
        ),
        Index("ix_class_schedule_teacher_id", "teacher_id"),
        Index("ix_class_schedule_gym_class_id", "gym_class_id"),
        Index("ix_class_schedule_start_date_time", "start_date", "start_time"),
    )

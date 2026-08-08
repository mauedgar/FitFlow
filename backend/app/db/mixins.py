"""Mixins reutilizables para los modelos ORM de FitFlow."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """Añade columnas de auditoría temporal a un modelo.

    Attributes:
        created_at: Momento de creación del registro.
        updated_at: Momento de la última actualización del registro.

    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ActiveMixin:
    """Añade un flag de activación lógica al modelo.

    Attributes:
        active: Indica si el registro se encuentra activo
            operativamente.

    """

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )


class SoftDeleteMixin:
    """Añade soporte para borrado lógico (soft delete).

    Attributes:
        deleted_at: Fecha en la que el registro fue marcado como
            eliminado lógicamente. ``None`` indica que no fue eliminado.

    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

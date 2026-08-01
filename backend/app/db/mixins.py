from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """
    Añade columnas de auditoría temporal a un modelo.

    - created_at: momento de creación del registro.
    - updated_at: momento de la última actualización del registro.
    """
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


class ActiveMixin:
    """
    Añade un flag de activación lógica al modelo.

    Este campo permite habilitar o deshabilitar operativamente
    un registro sin eliminarlo de la base de datos.
    """
    active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )


class SoftDeleteMixin:
    """
    Añade soporte para borrado lógico (soft delete).

    Cuando deleted_at tiene valor, el registro se considera eliminado
    a nivel lógico, pero permanece en la base de datos para trazabilidad
    e informes históricos.
    """
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
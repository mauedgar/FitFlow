"""
Schemas Base (Sprint 6–7)
-------------------------
Incluye:
• IDSchema
• TimestampSchema
• SoftDeleteSchema
• PublicIDSchema
• PublicTimestampSchema
• OperationalSchema
• AuditSchema (opcional)
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# --------------------------------------------------------------------------- #
# 1. ID base
# --------------------------------------------------------------------------- #

class IDSchema(BaseModel):
    """Esquema base con identificador único."""
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Timestamps base
# --------------------------------------------------------------------------- #

class TimestampSchema(BaseModel):
    """Timestamps completos para modelos privados/operativos."""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 3. Soft delete base
# --------------------------------------------------------------------------- #

class SoftDeleteSchema(BaseModel):
    """Campos de soft-delete y estado activo."""
    deleted_at: datetime | None = None
    active: bool = True
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 4. Versión pública de ID
# --------------------------------------------------------------------------- #

class PublicIDSchema(BaseModel):
    """Versión pública del ID (sin soft-delete)."""
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 5. Versión pública de timestamps
# --------------------------------------------------------------------------- #

class PublicTimestampSchema(BaseModel):
    """Timestamps públicos (solo created_at)."""
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 6. Esquema operativo completo
# --------------------------------------------------------------------------- #

class OperationalSchema(IDSchema, TimestampSchema, SoftDeleteSchema):
    """
    Esquema completo para modelos operativos internos.
    Incluye:
        • id
        • created_at
        • updated_at
        • deleted_at
        • active
    """
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 7. Auditoría (opcional para Sprint 7)
# --------------------------------------------------------------------------- #

class AuditSchema(BaseModel):
    """
    Esquema base para auditoría de cambios.
    Usado en:
        • reservas
        • sesiones
        • membresías
        • cambios de estado
    """
    changed_at: datetime
    changed_by: UUID
    previous_value: str | None = None
    new_value: str | None = None

    model_config = ConfigDict(from_attributes=True)

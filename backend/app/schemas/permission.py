from pydantic import BaseModel


class PermissionBase(BaseModel):
    """Campos comunes para los permisos."""

    id: str
    description: str | None = None


class PermissionCreate(PermissionBase):
    """Schema para crear un permiso."""


class PermissionUpdate(BaseModel):
    """Schema para actualizar un permiso."""

    description: str | None = None

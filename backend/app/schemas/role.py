from pydantic import BaseModel


class RoleBase(BaseModel):
    """Campos comunes del rol."""

    id: str
    description: str | None = None


class RoleCreate(RoleBase):
    """Schema para crear un rol."""



class RoleUpdate(BaseModel):
    """Schema para actualizar un rol."""

    description: str | None = None

# backend/app/schemas/user.py

import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.user import UserRole # Importamos el Enum del modelo

# Propiedades compartidas que tienen todos los esquemas
class UserBase(BaseModel):
    email: EmailStr
# Esquema para la creación de un usuario (lo que recibe la API)
class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.CLIENT
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None    
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
# Esquema para la respuesta de la API (lo que enviamos al frontend)
# NUNCA debe incluir la contraseña.
class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Permite que Pydantic lea datos desde modelos de SQLAlchemy



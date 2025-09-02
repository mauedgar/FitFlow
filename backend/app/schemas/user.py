# backend/app/schemas/user.py

import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.user import UserRole # Importamos el Enum del modelo

# Propiedades compartidas que tienen todos los esquemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Esquema para la creación de un usuario (lo que recibe la API)
class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.CLIENT

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

# Esquema para el token JWT que devolvemos al hacer login
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para los datos que van DENTRO del token
class TokenData(BaseModel):
    email: Optional[str] = None

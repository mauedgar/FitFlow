from pydantic import BaseModel
from typing import Optional

# Esquema para el token JWT que devolvemos al hacer login
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para los datos que van DENTRO del token
class TokenPayload(BaseModel):
    sub: Optional[str] = None   #email
    role: Optional[str] = None # Para el control de roles
    exp: Optional[int] = None  # Expiración del token
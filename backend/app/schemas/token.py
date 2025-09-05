from pydantic import BaseModel
from typing import Optional

# Esquema para el token JWT que devolvemos al hacer login
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para los datos que van DENTRO del token
class TokenData(BaseModel):
    email: Optional[str] = None

from pydantic import BaseModel


# Esquema para el token JWT que devolvemos al hacer login
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para los datos que van DENTRO del token
class TokenPayload(BaseModel):
    sub: None | str = None   #email
    role: None | str = None # Para el control de roles
    exp: None | int = None  # Expiración del token
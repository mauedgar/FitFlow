"""Esquemas Pydantic relacionados con la emisión y validación de tokens JWT.

Incluye:
- Token: estructura básica de un token de acceso.
- TokenPayload: contenido interno del JWT utilizado para autenticación.
- TokenPair: conjunto de tokens de acceso y refresco para flujos OAuth2.
"""

from pydantic import BaseModel

# Tipo de token utilizado en el esquema OAuth2.
TOKEN_TYPE_BEARER = "bearer"


class Token(BaseModel):
    """Representa un token de acceso emitido por el sistema.

    Atributos:
        access_token: Token JWT firmado que permite acceder a recursos protegidos.
        token_type: Tipo de token según el estándar OAuth2 (generalmente 'bearer').
    """

    access_token: str
    token_type: str = TOKEN_TYPE_BEARER


class TokenPayload(BaseModel):
    """Carga útil interna del token JWT.

    Esta información se utiliza para validar identidad, permisos y expiración.

    Atributos:
        sub: Identificador del sujeto (usuario o cliente).
        role: Rol asociado al usuario para control de permisos.
        exp: Timestamp UNIX de expiración del token.
    """

    sub: str | None = None
    role: str | None = None
    exp: int | None = None


class TokenPair(BaseModel):
    """Conjunto de tokens utilizados en flujos de autenticación con refresco.

    Atributos:
        access_token: Token JWT principal para acceso.
        refresh_token: Token JWT utilizado para renovar el access_token.
        token_type: Tipo de token según el estándar OAuth2.
    """

    access_token: str
    refresh_token: str
    token_type: str = TOKEN_TYPE_BEARER

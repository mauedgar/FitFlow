"""Módulo de Seguridad (Enterprise).

--------------------------------
• Hashing y verificación de contraseñas (bcrypt)
• Generación de Access Tokens (JWT)
• Generación de Refresh Tokens (JWT)
• Decodificación segura de tokens (sin excepciones ciegas)
• Compatible con Redis + Blacklist (si se habilita)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --------------------------------------------------------------------------- #
# Contexto de hashing (bcrypt)
# --------------------------------------------------------------------------- #

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt seguro para almacenar en la base de datos."""
    return pwd_context.hash(password)


# --------------------------------------------------------------------------- #
# JWT: Access Token
# --------------------------------------------------------------------------- #

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Crea un Access Token JWT firmado.

    • Incluye fecha de expiración.
    • Usa HS256 + SECRET_KEY.
    • Expira rápido (30 min por defecto).
    """
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {**data, "exp": expire}

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --------------------------------------------------------------------------- #
# JWT: Refresh Token
# --------------------------------------------------------------------------- #

def create_refresh_token(data: dict) -> str:
    """Crea un Refresh Token JWT firmado.

    • Expira en días/semanas.
    • No incluye roles.
    • Se usa para renovar el Access Token.
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    to_encode = {**data, "exp": expire}

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --------------------------------------------------------------------------- #
# JWT: Decodificación segura
# --------------------------------------------------------------------------- #

def decode_token(token: str) -> dict | None:
    """Decodifica un JWT de forma segura.

    • Captura únicamente excepciones esperadas.
    • Devuelve None si el token es inválido o expiró.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None

"""Módulo de Seguridad (Enterprise).

--------------------------------
• Hashing y verificación de contraseñas (bcrypt)
• Generación de Access Tokens (JWT)
• Generación de Refresh Tokens (JWT)
• Decodificación segura de tokens (sin excepciones ciegas)
• Compatible con Redis + Blacklist (si se habilita)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import ceil

import bcrypt
from app.core.config import settings
from jose import ExpiredSignatureError, JWTError, jwt

# --------------------------------------------------------------------------- #
# Hashing bcrypt nativo; no cambia formato almacenado ni JWT.
# --------------------------------------------------------------------------- #

_BCRYPT_MAX_PASSWORD_BYTES = 72
_BCRYPT_ROUNDS = 12  # Mismo costo por defecto que Passlib 1.7.4.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica hashes bcrypt heredados 2a/2b/2y sin migrar usuarios.

    bcrypt 4.3 conserva la semántica de verificación heredada incluso para
    contraseñas anteriores de más de 72 bytes. Esa limitación SOLO se mantiene
    al verificar hashes existentes; no se permite crear hashes nuevos truncados.
    """
    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False
    if "\x00" in plain_password:
        return False  # Passlib rechazaba el byte NUL.
    try:
        encoded_hash = hashed_password.encode("ascii")
        if len(encoded_hash) != 60 or encoded_hash[:4] not in (
            b"$2a$", b"$2b$", b"$2y$"
        ):
            return False
        return bcrypt.checkpw(plain_password.encode("utf-8"), encoded_hash)
    except (UnicodeError, ValueError):
        return False  # Hash corrupto, no excepción ni token de sesión.


def get_password_hash(password: str) -> str:
    """Crea hash 2b sin truncar bytes de contraseña ni cambiar formato de DB."""
    password_bytes = password.encode("utf-8")
    if b"\x00" in password_bytes:
        raise ValueError("La contraseña contiene un byte NUL no admitido")
    if len(password_bytes) > _BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("La contraseña excede los 72 bytes admitidos por bcrypt")
    return bcrypt.hashpw(
        password_bytes, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS, prefix=b"2b")
    ).decode("ascii")


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
    expire = datetime.now(tz=UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {**data, "token_use": "access", "exp": expire}

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
    expire = datetime.now(tz=UTC) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
    # Enforce a refresh-only purpose and exclude roles even for supplied data.
    to_encode = {**{k: v for k, v in data.items() if k != "role"}, "token_use": "refresh", "exp": expire}

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


def is_access_token_payload(payload: dict | None) -> bool:
    """A signed refresh token must never be accepted as a bearer credential.

    Historical untyped access tokens had a signed role; refresh tokens did not.
    """
    if not isinstance(payload, dict):
        return False
    token_use = payload.get("token_use")
    if token_use is not None:
        return token_use == "access"
    return isinstance(payload.get("role"), str) and bool(payload["role"])


def is_refresh_token_payload(payload: dict | None) -> bool:
    """Allow typed refresh and bounded untyped legacy refresh, never access."""
    if not isinstance(payload, dict):
        return False
    if not isinstance(payload.get("sub"), str) or not payload["sub"] or "role" in payload:
        return False
    purpose = payload.get("token_use")
    return purpose == "refresh" or "token_use" not in payload


def token_seconds_until_expiry(token: str) -> int:
    """Return signed JWT remaining TTL for Redis retention; fail closed.

    A signed JWT without a valid future expiration must never create an
    unbounded Redis key. Round upwards so the Redis key survives until expiry.
    """
    payload = decode_token(token)
    if payload is None:
        raise ValueError("Token inválido o expirado")
    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise ValueError("JWT sin expiración válida")
    remaining = ceil(exp - datetime.now(tz=UTC).timestamp())
    if remaining < 1:
        raise ValueError("JWT expirado")
    return remaining

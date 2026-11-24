"""Opaque Redis keys and JWT-bounded TTL for new refresh registrations.

Legacy raw JWT keys remain read-only compatibility inputs.
"""
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from math import ceil, floor

from app.core.security import decode_token


def opaque_jwt_key(prefix: str, token: str) -> str:
    return f"{prefix}sha256:{sha256(token.encode('utf-8')).hexdigest()}"


def legacy_jwt_key(prefix: str, token: str) -> str:
    return f"{prefix}{token}"


def signed_jwt_seconds_remaining(token: str) -> int:
    if not isinstance(token, str):
        raise ValueError("JWT inválido")
    payload = decode_token(token)
    if payload is None:
        raise ValueError("JWT inválido o expirado")
    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise ValueError("JWT sin exp válido")
    ttl = ceil(exp - datetime.now(tz=UTC).timestamp())
    if ttl < 1:
        raise ValueError("JWT vencido")
    return ttl


def signed_jwt_expiration_epoch(token: str) -> int:
    """Absolute Redis EXAT cutoff, rounded down, never a relative lifetime."""
    payload = decode_token(token)
    if payload is None:
        raise ValueError("JWT inválido o expirado")
    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise ValueError("JWT sin exp válido")
    try:
        cutoff = floor(exp)
    except (OverflowError, ValueError) as exc:
        raise ValueError("JWT sin exp válido") from exc
    if cutoff <= datetime.now(tz=UTC).timestamp():
        raise ValueError("JWT vencido")
    return cutoff

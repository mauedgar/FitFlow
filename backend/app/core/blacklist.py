"""Utilidades para gestionar la lista negra de tokens JWT.

Este módulo permite invalidar tokens antes de su expiración natural,
utilizando Redis como almacenamiento rápido. Se emplea para implementar
logout, revocación de tokens comprometidos y control de seguridad.
"""

from redis.exceptions import RedisError

from app.core.redis_client import get_redis_client
from app.core.security import token_seconds_until_expiry
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key
from app.services.errors import ExternalServiceError

# Prefijo utilizado para almacenar tokens invalidados en Redis.
BLACKLIST_PREFIX = "blacklist_token:"


def blacklist_token(token: str) -> None:
    """Agrega un token a la lista negra.

    El token queda marcado como inválido en Redis, impidiendo su uso
    posterior incluso si aún no expiró.

    Args:
        token: Token JWT que debe ser invalidado.

    """
    ttl = token_seconds_until_expiry(token)
    try:
        get_redis_client().set(opaque_jwt_key(BLACKLIST_PREFIX, token), "1", ex=ttl)
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc


def is_token_blacklisted(token: str) -> bool:
    """Verifica si un token se encuentra en la lista negra.

    Args:
        token: Token JWT a consultar.

    Returns:
        True si el token está invalidado; False en caso contrario.

    """
    try:
        client = get_redis_client()
        return (
            client.exists(opaque_jwt_key(BLACKLIST_PREFIX, token)) == 1
            or client.exists(legacy_jwt_key(BLACKLIST_PREFIX, token)) == 1
        )
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc

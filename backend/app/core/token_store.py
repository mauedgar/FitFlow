"""Gestión de tokens de refresco en Redis.

Este módulo permite almacenar, validar y eliminar tokens de refresco
utilizados en el flujo de autenticación OAuth2.
"""

from redis.exceptions import RedisError

from app.core.redis_client import get_redis_client
from app.core.security import token_seconds_until_expiry
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key
from app.services.errors import ExternalServiceError

# Prefijo para las claves de tokens de refresco en Redis.
REFRESH_PREFIX = "refresh_token:"


def store_refresh_token(user_id: str, token: str) -> None:
    """Guarda un token de refresco asociado a un usuario.

    Args:
        user_id: Identificador único del usuario.
        token: Token de refresco emitido por el sistema.

    """
    ttl = token_seconds_until_expiry(token)
    try:
        get_redis_client().set(opaque_jwt_key(REFRESH_PREFIX, token), user_id, ex=ttl)
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc


def is_refresh_token_valid(token: str) -> bool:
    """Verifica si un token de refresco existe y es válido.

    Args:
        token: Token de refresco a verificar.

    Returns:
        True si el token está almacenado en Redis; False en caso contrario.

    """
    try:
        client = get_redis_client()
        return (
            client.exists(opaque_jwt_key(REFRESH_PREFIX, token)) == 1
            or client.exists(legacy_jwt_key(REFRESH_PREFIX, token)) == 1
        )
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc


def delete_refresh_token(token: str) -> None:
    """Elimina un token de refresco del almacenamiento Redis.

    Args:
        token: Token de refresco que debe invalidarse.

    """
    try:
        get_redis_client().delete(
            opaque_jwt_key(REFRESH_PREFIX, token),
            legacy_jwt_key(REFRESH_PREFIX, token),
        )
    except RedisError as exc:
        raise ExternalServiceError("Redis no está disponible.") from exc

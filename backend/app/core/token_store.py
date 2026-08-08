"""Gestión de tokens de refresco en Redis.

Este módulo permite almacenar, validar y eliminar tokens de refresco
utilizados en el flujo de autenticación OAuth2.
"""

from app.core.redis_client import redis_client

# Prefijo para las claves de tokens de refresco en Redis.
REFRESH_PREFIX = "refresh_token:"


def store_refresh_token(user_id: str, token: str) -> None:
    """Guarda un token de refresco asociado a un usuario.

    Args:
        user_id: Identificador único del usuario.
        token: Token de refresco emitido por el sistema.

    """
    redis_client.set(f"{REFRESH_PREFIX}{token}", user_id)


def is_refresh_token_valid(token: str) -> bool:
    """Verifica si un token de refresco existe y es válido.

    Args:
        token: Token de refresco a verificar.

    Returns:
        True si el token está almacenado en Redis; False en caso contrario.

    """
    return redis_client.exists(f"{REFRESH_PREFIX}{token}") == 1


def delete_refresh_token(token: str) -> None:
    """Elimina un token de refresco del almacenamiento Redis.

    Args:
        token: Token de refresco que debe invalidarse.

    """
    redis_client.delete(f"{REFRESH_PREFIX}{token}")

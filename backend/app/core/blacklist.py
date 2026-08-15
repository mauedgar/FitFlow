"""Utilidades para gestionar la lista negra de tokens JWT.

Este módulo permite invalidar tokens antes de su expiración natural,
utilizando Redis como almacenamiento rápido. Se emplea para implementar
logout, revocación de tokens comprometidos y control de seguridad.
"""

from app.core.redis_client import get_redis_client

# Prefijo utilizado para almacenar tokens invalidados en Redis.
BLACKLIST_PREFIX = "blacklist_token:"


def blacklist_token(token: str) -> None:
    """Agrega un token a la lista negra.

    El token queda marcado como inválido en Redis, impidiendo su uso
    posterior incluso si aún no expiró.

    Args:
        token: Token JWT que debe ser invalidado.

    """
    get_redis_client().set(f"{BLACKLIST_PREFIX}{token}", "1")


def is_token_blacklisted(token: str) -> bool:
    """Verifica si un token se encuentra en la lista negra.

    Args:
        token: Token JWT a consultar.

    Returns:
        True si el token está invalidado; False en caso contrario.

    """
    return get_redis_client().exists(f"{BLACKLIST_PREFIX}{token}") == 1

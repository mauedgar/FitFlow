"""Utilidades para gestionar la lista negra de tokens JWT.

Este módulo permite invalidar tokens antes de su expiración natural,
utilizando Redis como almacenamiento rápido. Se emplea para implementar
logout, revocación de tokens comprometidos y control de seguridad.
"""

from app.core.redis_client import execute_redis_command, token_redis_fingerprint
from app.core.security import token_remaining_ttl

# Prefijo utilizado para almacenar tokens invalidados en Redis.
BLACKLIST_PREFIX = "blacklist_token:"


def blacklist_key(token: str) -> str:
    return f"{BLACKLIST_PREFIX}hmac:{token_redis_fingerprint(token)}"


def legacy_blacklist_key(token: str) -> str:
    return f"{BLACKLIST_PREFIX}{token}"


def blacklist_token(token: str) -> None:
    """Agrega un token a la lista negra.

    El token queda marcado como inválido en Redis, impidiendo su uso
    posterior incluso si aún no expiró.

    Args:
        token: Token JWT que debe ser invalidado.

    """
    remaining = token_remaining_ttl(token)
    execute_redis_command(
        lambda client: client.set(blacklist_key(token), "1", ex=remaining)
    )


def is_token_blacklisted(token: str) -> bool:
    """Verifica si un token se encuentra en la lista negra.

    Args:
        token: Token JWT a consultar.

    Returns:
        True si el token está invalidado; False en caso contrario.

    """
    return execute_redis_command(
        lambda client: bool(
            client.exists(blacklist_key(token))
            or client.exists(legacy_blacklist_key(token))
        )
    )

"""Gestión de tokens de refresco en Redis.

Este módulo permite almacenar, validar y eliminar tokens de refresco
utilizados en el flujo de autenticación OAuth2.
"""

from app.core.redis_client import execute_redis_command, token_redis_fingerprint
from app.core.security import token_remaining_ttl

# Prefijo para las claves de tokens de refresco en Redis.
REFRESH_PREFIX = "refresh_token:"
PENDING_PREFIX = "refresh_pending:"
PENDING_SECONDS = 120

# Atomically acknowledge once, or repeat an already accepted acknowledgement.
# The active key TTL never exceeds the remaining signed JWT lifetime.
_ACTIVATE_PENDING_LUA = """
local active = redis.call("GET", KEYS[1])
if active then
  if active == ARGV[1] then return 1 else return 0 end
end
if redis.call("GET", KEYS[2]) ~= ARGV[1] then return 0 end
redis.call("SET", KEYS[1], ARGV[1], "EX", tonumber(ARGV[2]))
redis.call("DEL", KEYS[2])
return 1
"""



def refresh_token_key(token: str) -> str:
    return f"{REFRESH_PREFIX}hmac:{token_redis_fingerprint(token)}"


def pending_refresh_token_key(token: str) -> str:
    return f"{PENDING_PREFIX}hmac:{token_redis_fingerprint(token)}"


def legacy_refresh_token_key(token: str) -> str:
    return f"{REFRESH_PREFIX}{token}"


def store_refresh_token(user_id: str, token: str) -> None:
    """Guarda un token de refresco asociado a un usuario.

    Args:
        user_id: Identificador único del usuario.
        token: Token de refresco emitido por el sistema.

    """
    remaining = token_remaining_ttl(token)
    execute_redis_command(
        lambda client: client.set(refresh_token_key(token), user_id, ex=remaining)
    )


def store_pending_refresh_token(user_id: str, token: str) -> None:
    """Negotiated ack-v1 login: undelivered refresh tokens get a short lease.

    Pending credentials cannot refresh access and expire without client acknowledgement.
    Legacy clients still receive the existing active-token behavior.
    """
    remaining = token_remaining_ttl(token)
    execute_redis_command(
        lambda client: client.set(
            pending_refresh_token_key(token), user_id,
            ex=min(PENDING_SECONDS, remaining),
        )
    )


def activate_pending_refresh_token(user_id: str, token: str) -> bool:
    """Promote a pending credential with an atomic, owner-bound idempotent ACK."""
    remaining = token_remaining_ttl(token)
    return bool(execute_redis_command(
        lambda client: client.eval(
            _ACTIVATE_PENDING_LUA, 2,
            refresh_token_key(token), pending_refresh_token_key(token),
            user_id, remaining,
        )
    ))


def is_refresh_token_valid(token: str) -> bool:
    """Verifica si un token de refresco existe y es válido.

    Args:
        token: Token de refresco a verificar.

    Returns:
        True si el token está almacenado en Redis; False en caso contrario.

    """
    return execute_redis_command(
        lambda client: bool(
            client.exists(refresh_token_key(token))
            or (
                _legacy_lookup_required(token)
                and client.exists(legacy_refresh_token_key(token))
            )
        )
    )


def delete_refresh_token(token: str) -> None:
    """Elimina un token de refresco del almacenamiento Redis.

    Args:
        token: Token de refresco que debe invalidarse.

    """
    execute_redis_command(
        lambda client: client.delete(
            refresh_token_key(token),
            pending_refresh_token_key(token),
            *([legacy_refresh_token_key(token)] if _legacy_lookup_required(token) else []),
        )
    )

def _legacy_lookup_required(token: str) -> bool:
    """Only pre-jti refresh issuances can have legacy raw-token Redis keys."""
    from app.core.security import decode_token

    payload = decode_token(token)
    return payload is not None and not payload.get("jti")

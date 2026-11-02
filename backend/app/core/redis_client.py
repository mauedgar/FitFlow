from app.core.config import settings
from app.services.errors import ExternalServiceError
from redis import Redis
from redis.exceptions import RedisError


def get_redis_client() -> Redis:
    """Create a Redis client only when an operation actually requires it."""
    if settings.REDIS_URL is None:
        raise ExternalServiceError("Redis no está configurado.")
    try:
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except RedisError as err:
        raise ExternalServiceError("Redis no está disponible.") from err



def token_redis_fingerprint(token: str) -> str:
    """HMAC token identifier; raw bearer credentials never enter new Redis keys."""
    import hashlib
    import hmac

    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def execute_redis_command(command):
    """Normalize Redis failures even when they occur after a successful ping."""
    client = get_redis_client()
    try:
        try:
            return command(client)
        except RedisError as err:
            raise ExternalServiceError("Redis no está disponible.") from err
    finally:
        client.close()

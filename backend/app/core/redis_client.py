from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.services.errors import ExternalServiceError



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

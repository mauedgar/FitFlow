from redis import Redis

from app.core.config import settings

if settings.REDIS_URL is None:
    msg = "REDIS_URL no está configurado en el entorno."
    raise RuntimeError(msg)

redis_client = Redis.from_url(settings.REDIS_URL)

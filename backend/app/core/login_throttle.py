"""Bounded login throttling: atomic Redis window, synthetic test opt-in."""

from __future__ import annotations

from app.core.config import settings
from app.core.redis_client import execute_redis_command, token_redis_fingerprint
from fastapi import HTTPException, status

LIMIT = 10
WINDOW_SECONDS = 60
_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
return count
"""


def login_rate_key(username: str, remote: str) -> str:
    """Opaque deterministic key; no email, raw credentials or IP in Redis key."""
    return "auth_login_rate:hmac:" + token_redis_fingerprint(
        remote + ":" + username.strip().casefold()
    )


def check_login_throttle(username: str, remote: str) -> None:
    """Fail closed on Redis outage in non-test modes, with bounded 429."""
    if settings.TESTING:
        return
    count = execute_redis_command(
        lambda client: client.eval(
            _LUA, 1, login_rate_key(username, remote), WINDOW_SECONDS,
        )
    )
    if int(count) > LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intentá nuevamente más tarde.",
            headers={"Retry-After": str(WINDOW_SECONDS)},
        )

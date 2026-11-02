"""Bounded atomic Redis login limiter: per-origin and cross-origin account caps."""

from __future__ import annotations

from app.core.config import settings
from app.core.redis_client import execute_redis_command, token_redis_fingerprint
from fastapi import HTTPException, status

LIMIT = 10
ACCOUNT_LIMIT = 30
WINDOW_SECONDS = 60
_LUA = """
local a = redis.call('INCR', KEYS[1])
if a == 1 then redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1])) end
local b = redis.call('INCR', KEYS[2])
if b == 1 then redis.call('EXPIRE', KEYS[2], tonumber(ARGV[1])) end
return {a, b, redis.call('TTL', KEYS[1]), redis.call('TTL', KEYS[2])}
"""


def login_rate_key(username: str, remote: str) -> str:
    """Do not expose email, IP or credentials in Redis keys."""
    return "auth_login_rate:hmac:" + token_redis_fingerprint(
        remote + ":" + username.strip().casefold()
    )


def account_rate_key(username: str) -> str:
    """Limit distributed guessing of the same account across remote origins."""
    return "auth_login_account:hmac:" + token_redis_fingerprint(
        username.strip().casefold()
    )


def check_login_throttle(username: str, remote: str) -> None:
    """Fail closed on Redis outage, returning an exact remaining Retry-After."""
    if settings.TESTING:
        return
    count, account_count, ip_ttl, account_ttl = execute_redis_command(
        lambda client: client.eval(
            _LUA, 2, login_rate_key(username, remote),
            account_rate_key(username), WINDOW_SECONDS,
        )
    )
    if int(count) > LIMIT or int(account_count) > ACCOUNT_LIMIT:
        retry_after = (
            int(ip_ttl) if int(count) > LIMIT else int(account_ttl)
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intentá nuevamente más tarde.",
            headers={"Retry-After": str(max(1, retry_after))},
        )

"""Dependency probes for the traffic-readiness endpoint."""

import asyncio

from sqlalchemy import text

from app.core.redis_client import get_redis_client
from app.db.session import engine


async def _check_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


def _check_redis() -> None:
    client = get_redis_client()
    client.close()


async def get_unavailable_dependencies() -> list[str]:
    """Return only dependency names, never connection or secret details."""
    checks = (
        ("database", _check_database()),
        ("redis", asyncio.to_thread(_check_redis)),
    )
    results = await asyncio.gather(*(check for _, check in checks), return_exceptions=True)
    return [name for (name, _), result in zip(checks, results, strict=True) if isinstance(result, BaseException)]

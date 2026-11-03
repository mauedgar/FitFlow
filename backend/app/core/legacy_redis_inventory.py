"""Bounded read-only inventory of legacy plaintext token Redis keys."""
from __future__ import annotations

import argparse
import json
import os

from app.core.config import settings
from redis import Redis
from redis.exceptions import RedisError

PREFIXES = ("refresh_token:", "blacklist_token:")

def summarize_legacy_keys(client: object, max_pages: int = 12) -> dict[str, dict[str, int | bool]]:
    if not 1 <= max_pages <= 40:
        raise ValueError("unbounded scan not permitted")
    result: dict[str, dict[str, int | bool]] = {}
    for prefix in PREFIXES:
        counts: dict[str, int | bool] = {
            "raw_no_ttl": 0, "raw_has_ttl": 0,
            "hmac_no_ttl": 0, "hmac_has_ttl": 0,
            "expired_during_scan": 0, "pages": 0, "partial": False,
        }
        cursor = 0
        for _ in range(max_pages):
            cursor, keys = client.scan(cursor=cursor, match=f"{prefix}*", count=64)  # type: ignore[attr-defined]
            counts["pages"] = int(counts["pages"]) + 1
            for raw in keys:
                # Redis keys are arbitrary bytes. Decode neither raw bearer-key
                # names nor a possibly malformed historical UTF-8 payload.
                is_modern = (
                    raw.startswith((prefix + "hmac:").encode("ascii"))
                    if isinstance(raw, bytes)
                    else str(raw).startswith(prefix + "hmac:")
                )
                variant = "hmac" if is_modern else "raw"
                ttl = client.ttl(raw)  # type: ignore[attr-defined]
                label = "expired_during_scan" if ttl == -2 else (
                    variant + ("_no_ttl" if ttl == -1 else "_has_ttl")
                )
                counts[label] = int(counts[label]) + 1
            if not cursor:
                break
        counts["partial"] = bool(cursor)
        result[prefix.removesuffix(":")] = counts
    return result

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ack-read-only", action="store_true")
    p.add_argument("--max-pages", type=int, default=12)
    a = p.parse_args()
    if not a.ack_read_only or os.getenv("FITFLOW_ALLOW_LEGACY_READONLY_INVENTORY") != "1":
        p.error("explicit read-only authorization required")
    if not 1 <= a.max_pages <= 40:
        p.error("bounded pages only")
    url = settings.REDIS_URL
    if url is None:
        print("LEGACY_INVENTORY_UNAVAILABLE")
        return 2
    client = None
    try:
        # Unlike application Redis clients this must not decode raw key bytes.
        client = Redis.from_url(
            url, decode_responses=False, socket_connect_timeout=3,
            socket_timeout=5,
        )
        client.ping()
        print(json.dumps({
            "read_only": True,
            "raw_keys_or_values_disclosed": False,
            "report": summarize_legacy_keys(client, a.max_pages),
        }, sort_keys=True))
        return 0
    except (RedisError, ValueError):
        # Avoid exposing service details and token-bearing key names.
        print("LEGACY_INVENTORY_UNAVAILABLE")
        return 2
    finally:
        if client is not None:
            client.close()

if __name__ == "__main__":
    raise SystemExit(main())

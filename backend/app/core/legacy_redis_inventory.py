"""Test-only bounded read-only inventory of legacy plaintext token Redis keys."""
from __future__ import annotations

import argparse
import json
import os

from app.core.redis_client import get_redis_client

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
                key = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                variant = "hmac" if key.startswith(prefix + "hmac:") else "raw"
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
    client = None
    try:
        client = get_redis_client()
        print(json.dumps({
            "read_only": True,
            "raw_keys_or_values_disclosed": False,
            "report": summarize_legacy_keys(client, a.max_pages),
        }, sort_keys=True))
        return 0
    except Exception:
        # Avoid exposing service details and token-bearing key names.
        print("LEGACY_INVENTORY_UNAVAILABLE")
        return 2
    finally:
        if client is not None:
            client.close()

if __name__ == "__main__":
    raise SystemExit(main())

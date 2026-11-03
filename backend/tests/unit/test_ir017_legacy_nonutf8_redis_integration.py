"""IR017 byte-safe scan exercised against disposable Redis only."""
from __future__ import annotations

from urllib.parse import urlparse
from uuid import uuid4

import pytest
from app.core.config import settings
from app.core.legacy_redis_inventory import summarize_legacy_keys
from redis import Redis

pytestmark = [pytest.mark.integration]


def test_inventory_handles_undecodable_redis_key_without_printing_it() -> None:
    assert settings.TESTING is True
    url = settings.REDIS_URL
    if url is None or urlparse(url).hostname not in {"127.0.0.1", "localhost"}:
        pytest.skip("Strictly disposable loopback Redis test fixture")
    client = Redis.from_url(url, decode_responses=False)
    key = b"refresh_token:\xffir017-synthetic-only-" + uuid4().hex.encode("ascii")
    try:
        client.set(key, b"synthetic-fixture-no-jwt", ex=30)
        counts = summarize_legacy_keys(client, max_pages=40)
        assert counts["refresh_token"]["raw_has_ttl"] >= 1
        assert counts["refresh_token"]["partial"] is False
        assert "ir017-synthetic" not in str(counts)
    finally:
        # Unit/integration fixture cleanup is permitted only in disposable CI.
        client.delete(key)
        client.close()

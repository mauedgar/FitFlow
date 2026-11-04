"""No live Redis; classify legacy raw-key TTLs without disclosing bearer names."""

from __future__ import annotations

import pytest
from app.core.legacy_redis_inventory import summarize_legacy_keys


class FakeRedis:
    def __init__(self, partial: bool = False) -> None:
        self.partial = partial
        self.operations: list[str] = []
    def scan(self, *, cursor: int, match: str, count: int) -> tuple[int, list[str | bytes]]:
        self.operations.append("scan")
        assert count == 64
        keys: list[str | bytes]
        if match.startswith("refresh_token:"):
            keys = [
                "refresh_token:eyJ.secret-not-for-output",
                "refresh_token:hmac:nonbearer-fingerprint",
                b"refresh_token:\xffir017-invalid-utf8-test-only",
            ]
        else:
            keys = ["blacklist_token:eyJ.another-secret-not-for-output"]
        return (1 if self.partial else 0, keys)
    def ttl(self, key: str | bytes) -> int:
        self.operations.append("ttl")
        return -1 if isinstance(key, bytes) or ":eyJ." in key else 30
    def get(self, key: str) -> None:
        raise AssertionError("reading values forbidden")
    def delete(self, key: str) -> None:
        raise AssertionError("mutation forbidden")

def test_readonly_counts_and_key_redaction() -> None:
    fake = FakeRedis()
    summary = summarize_legacy_keys(fake)
    assert summary["refresh_token"]["raw_no_ttl"] == 2
    assert summary["refresh_token"]["hmac_has_ttl"] == 1
    assert summary["blacklist_token"]["raw_no_ttl"] == 1
    assert "eyJ" not in str(summary)
    assert "ir017-invalid-utf8" not in str(summary)
    assert set(fake.operations) == {"scan", "ttl"}

def test_bounded_partial_does_not_claim_complete() -> None:
    summary = summarize_legacy_keys(FakeRedis(partial=True), 2)
    assert summary["refresh_token"]["partial"] is True
    assert summary["blacklist_token"]["partial"] is True

def test_inventory_refuses_unbounded_read() -> None:
    with pytest.raises(ValueError, match="unbounded"):
        summarize_legacy_keys(FakeRedis(), 41)

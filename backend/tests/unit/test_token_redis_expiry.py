"""Bounded Redis lifetime of signed JWT credentials; synthetic only."""
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core import blacklist, security, token_store
from app.core.config import settings
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key


class FakeRedis:
    def __init__(self) -> None:
        self.sets: list[tuple[str, str, int]] = []

    def set(self, key: str, value: str, *, ex: int) -> None:
        self.sets.append((key, value, ex))


def test_redis_registration_and_blacklist_have_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(token_store, "get_redis_client", lambda: fake)
    monkeypatch.setattr(blacklist, "get_redis_client", lambda: fake)
    token = security.create_refresh_token({"sub": "synthetic-only"})
    token_store.store_refresh_token("synthetic-only", token)
    blacklist.blacklist_token(token)
    assert len(fake.sets) == 2
    assert fake.sets[0][0] == opaque_jwt_key("refresh_token:", token)
    assert fake.sets[1][0] == opaque_jwt_key("blacklist_token:", token)
    assert all(token not in key for key, _, _ in fake.sets)
    assert all(0 < ttl <= settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60 for _, _, ttl in fake.sets)


def test_unsigned_or_expired_or_missing_exp_cannot_write_unbounded_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(token_store, "get_redis_client", lambda: fake)
    monkeypatch.setattr(blacklist, "get_redis_client", lambda: fake)
    expired = jwt.encode(
        {"sub": "synthetic", "exp": datetime.now(tz=UTC) - timedelta(seconds=2)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    no_exp = jwt.encode({"sub": "synthetic"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    for token in ("not-a-jwt", expired, no_exp):
        with pytest.raises((TypeError, ValueError)):
            token_store.store_refresh_token("synthetic", token)
        with pytest.raises((TypeError, ValueError)):
            blacklist.blacklist_token(token)
    assert fake.sets == []


def test_legacy_keys_remain_readable_and_deletable_without_new_raw_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = security.create_refresh_token({"sub": "synthetic-legacy"})
    raw_refresh = legacy_jwt_key(token_store.REFRESH_PREFIX, token)
    raw_blacklist = legacy_jwt_key(blacklist.BLACKLIST_PREFIX, token)

    class LegacyRedis:
        def __init__(self) -> None:
            self.keys: set[str] = {raw_refresh, raw_blacklist}

        def exists(self, key: str) -> int:
            return int(key in self.keys)

        def delete(self, *keys: str) -> int:
            before = len(self.keys)
            self.keys.difference_update(keys)
            return before - len(self.keys)

    fake = LegacyRedis()
    monkeypatch.setattr(token_store, "get_redis_client", lambda: fake)
    monkeypatch.setattr(blacklist, "get_redis_client", lambda: fake)
    assert token_store.is_refresh_token_valid(token)
    assert blacklist.is_token_blacklisted(token)
    token_store.delete_refresh_token(token)
    assert not token_store.is_refresh_token_valid(token)
    assert raw_blacklist in fake.keys  # No legacy cleanup is performed here.

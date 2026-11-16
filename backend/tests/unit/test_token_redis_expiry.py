"""Bounded Redis lifetime of signed JWT credentials; synthetic only."""
from datetime import UTC, datetime, timedelta

import pytest
from redis.exceptions import RedisError
from jose import jwt

from app.core import blacklist, security, token_store
from app.core.config import settings
from app.core.token_keys import legacy_jwt_key, opaque_jwt_key
from app.services.errors import ExternalServiceError


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

@pytest.mark.parametrize(
    "operation",
    ("blacklist_write", "blacklist_lookup", "refresh_write", "refresh_lookup", "refresh_delete"),
)
def test_redis_post_ping_io_errors_become_external_service_errors(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Every token Redis operation normalizes an I/O failure after the client is obtained."""
    class BrokenAfterPingRedis:
        def set(self, *_args: object, **_kwargs: object) -> None:
            raise RedisError("synthetic post-ping SET failure")

        def exists(self, *_args: object) -> int:
            raise RedisError("synthetic post-ping EXISTS failure")

        def delete(self, *_args: object) -> int:
            raise RedisError("synthetic post-ping DELETE failure")

    broken = BrokenAfterPingRedis()
    monkeypatch.setattr(token_store, "get_redis_client", lambda: broken)
    monkeypatch.setattr(blacklist, "get_redis_client", lambda: broken)
    token = security.create_refresh_token({"sub": "synthetic-post-ping"})
    operations = {
        "blacklist_write": lambda: blacklist.blacklist_token(token),
        "blacklist_lookup": lambda: blacklist.is_token_blacklisted(token),
        "refresh_write": lambda: token_store.store_refresh_token("synthetic-post-ping", token),
        "refresh_lookup": lambda: token_store.is_refresh_token_valid(token),
        "refresh_delete": lambda: token_store.delete_refresh_token(token),
    }
    with pytest.raises(ExternalServiceError, match="Redis no está disponible"):
        operations[operation]()

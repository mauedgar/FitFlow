"""Bounded Redis lifetime of signed JWT credentials; synthetic only."""
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core import blacklist, security, token_store
from app.core.config import settings


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
    assert fake.sets[0][0].startswith("refresh_token:")
    assert fake.sets[1][0].startswith("blacklist_token:")
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
        with pytest.raises(ValueError):
            token_store.store_refresh_token("synthetic", token)
        with pytest.raises(ValueError):
            blacklist.blacklist_token(token)
    assert fake.sets == []

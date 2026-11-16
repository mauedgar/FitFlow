"""No network: signed sid handling and TTL of session revocation marker."""
import uuid

import pytest

from app.core import security, session_revocation
from app.core.config import settings


class FakeRedis:
    def __init__(self) -> None:
        self.entries: dict[str, tuple[str, int]] = {}

    def set(self, key: str, value: str, *, ex: int) -> None:
        self.entries[key] = (value, ex)

    def exists(self, key: str) -> int:
        return int(key in self.entries)


def test_session_revocation_key_is_opaque_and_expiring(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(session_revocation, "get_redis_client", lambda: redis)
    monkeypatch.setattr(session_revocation, "is_token_blacklisted", lambda _token: False)
    sid = str(uuid.uuid4())
    access = security.create_access_token({"sub": "synthetic", "role": "client", "sid": sid})
    refresh = security.create_refresh_token({"sub": "synthetic", "sid": sid})
    payload = security.decode_token(access)
    assert payload is not None
    assert not session_revocation.is_access_credential_revoked(access, payload)
    session_revocation.revoke_session(sid, refresh)
    assert session_revocation.is_access_credential_revoked(access, payload)
    assert len(redis.entries) == 1
    [(key, (_, ttl))] = redis.entries.items()
    assert sid not in key
    assert access not in key and refresh not in key
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 < ttl <= (
        settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        + session_revocation._REVOCATION_CLOCK_SKEW_SECONDS
    )


def test_invalid_or_missing_sids_never_pass_as_valid_sessions() -> None:
    for sid in ("not-a-uuid", "00000000-0000-0000-0000-000000000000", 12):
        assert session_revocation.is_session_revoked(sid)
        assert not session_revocation.session_ids_match(
            {"sid": sid}, {"sid": sid},
        )
    assert session_revocation.session_ids_match({"sub": "legacy"}, {"sub": "legacy"})
    assert not session_revocation.session_ids_match({"sid": str(uuid.uuid4())}, {})


def test_sid_tombstone_covers_latest_possible_access_after_refresh_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Logical Redis time crosses old refresh expiry without waiting in real time."""
    class ExpiringRedis:
        def __init__(self) -> None:
            self.now = 0
            self.deadlines: dict[str, int] = {}

        def set(self, key: str, _value: str, *, ex: int) -> None:
            assert ex > 0
            self.deadlines[key] = self.now + ex

        def exists(self, key: str) -> int:
            return int(self.now < self.deadlines.get(key, 0))

    redis = ExpiringRedis()
    monkeypatch.setattr(session_revocation, "get_redis_client", lambda: redis)
    monkeypatch.setattr(session_revocation, "is_token_blacklisted", lambda _token: False)
    # A valid signed refresh is represented as having one remaining second.
    # Only its remaining-TTL calculation is controlled; no JWT secret changes.
    monkeypatch.setattr(session_revocation, "token_seconds_until_expiry", lambda _token: 1)
    sid = str(uuid.uuid4())
    access = security.create_access_token({"sub": "synthetic", "role": "client", "sid": sid})
    refresh = security.create_refresh_token({"sub": "synthetic", "sid": sid})
    payload = security.decode_token(access)
    assert payload is not None

    session_revocation.revoke_session(sid, refresh)
    key = session_revocation._revocation_key(uuid.UUID(sid).hex)
    latest_access_lifetime = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert redis.deadlines[key] == (
        1 + latest_access_lifetime + session_revocation._REVOCATION_CLOCK_SKEW_SECONDS
    )
    redis.now = 2  # the old 1-second marker would already have disappeared
    assert session_revocation.is_access_credential_revoked(access, payload)
    redis.now = 1 + latest_access_lifetime
    assert session_revocation.is_access_credential_revoked(access, payload)
    redis.now = redis.deadlines[key]
    assert redis.exists(key) == 0  # only after the latest access plus buffer

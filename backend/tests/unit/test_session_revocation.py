"""No network: signed sid handling and TTL of session revocation marker."""
import uuid

import pytest

from app.core import security, session_revocation


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
    assert 0 < ttl <= 7 * 24 * 60 * 60


def test_invalid_or_missing_sids_never_pass_as_valid_sessions() -> None:
    for sid in ("not-a-uuid", "00000000-0000-0000-0000-000000000000", 12):
        assert session_revocation.is_session_revoked(sid)
        assert not session_revocation.session_ids_match(
            {"sid": sid}, {"sid": sid},
        )
    assert session_revocation.session_ids_match({"sub": "legacy"}, {"sub": "legacy"})
    assert not session_revocation.session_ids_match({"sid": str(uuid.uuid4())}, {})

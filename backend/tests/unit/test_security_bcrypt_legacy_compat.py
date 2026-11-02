"""Compatibility and negative-case contracts for native bcrypt replacement (#43).

All credentials and hashes in this file are synthetic; no user DB access.
"""

from __future__ import annotations

import bcrypt
import pytest

from app.core.security import get_password_hash, verify_password


def _synthetic_hash(password: str, prefix: bytes = b"2b") -> str:
    # Fixed bcrypt salt/cost makes cross-version checks reproducible.
    salt = b"$" + prefix + b"$04$abcdefghijklmnopqrstuu"
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("ascii")


@pytest.mark.parametrize("prefix", [b"2a", b"2b", b"2y"])
def test_legacy_bcrypt_prefixes_verify_without_rehash(prefix: bytes) -> None:
    password = "Prueba-Ñú!42"
    legacy_hash = _synthetic_hash(password, prefix=prefix)
    assert legacy_hash.startswith("$" + prefix.decode() + "$")
    assert verify_password(password, legacy_hash)
    assert not verify_password("incorrecta", legacy_hash)
    assert verify_password(password, legacy_hash)  # No writes or migration.


@pytest.mark.parametrize("password", ["", "simple", "mañana", "🦊" * 10, "a" * 72])
def test_new_bcrypt_hash_round_trip(password: str) -> None:
    digest = get_password_hash(password)
    assert digest.startswith("$2b$12$")
    assert len(digest) == 60
    assert verify_password(password, digest)
    if len(password.encode("utf-8")) < 72:
        assert not verify_password(password + "x", digest)


def test_bcrypt_byte_boundary_never_truncates_new_passwords() -> None:
    assert verify_password("a" * 72, get_password_hash("a" * 72))
    with pytest.raises(ValueError, match="72 bytes"):
        get_password_hash("a" * 73)
    assert verify_password("ñ" * 36, get_password_hash("ñ" * 36))
    with pytest.raises(ValueError, match="72 bytes"):
        get_password_hash("ñ" * 37)


def test_legacy_overlength_verification_is_preserved_without_new_hash_truncation() -> None:
    # Legacy Passlib 1.7.4 silently accepted >72 bytes on bcrypt hashes.
    # This path verifies existing hashes ONLY; creation rejects >72 bytes.
    digest = _synthetic_hash("a" * 72)
    assert verify_password("a" * 73, digest)
    with pytest.raises(ValueError):
        get_password_hash("a" * 73)


@pytest.mark.parametrize(
    "bad_hash",
    [
        "",
        "not-a-hash",
        "$2x$12$abcdefghijklmnopqrstuu" + "a" * 31,
        "$2b$99$abcdefghijklmnopqrstuu" + "a" * 31,
        "$2b$12$too-short",
        "🚫" * 60,
    ],
)
def test_invalid_hash_is_rejected_without_exception(bad_hash: str) -> None:
    assert verify_password("password", bad_hash) is False


def test_embedded_nul_rejected_like_legacy_passlib() -> None:
    digest = _synthetic_hash("password")
    assert not verify_password("password\x00", digest)
    with pytest.raises(ValueError, match="NUL"):
        get_password_hash("password\x00")


def test_unsupported_types_fail_closed_at_verification() -> None:
    assert not verify_password("pw", None)  # type: ignore[arg-type]
    assert not verify_password(None, "hash")  # type: ignore[arg-type]

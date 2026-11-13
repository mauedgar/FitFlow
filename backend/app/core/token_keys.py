"""Opaque Redis keys for JWTs: no new keys disclose bearer credentials.

Legacy raw JWT keys remain readable only for bounded backward compatibility.
Old stored data is not migrated/cleaned by deploying this code.
"""
from hashlib import sha256


def opaque_jwt_key(prefix: str, token: str) -> str:
    """Use a deterministic digest; the original signed token never enters the key."""
    digest = sha256(token.encode("utf-8")).hexdigest()
    return f"{prefix}sha256:{digest}"


def legacy_jwt_key(prefix: str, token: str) -> str:
    """Pre-transition Redis key, read/delete only, never write."""
    return f"{prefix}{token}"

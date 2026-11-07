"""Atomic public client signup without changing legacy account-only registration.

A new signup creates User + joined-inheritance Person/Client in one transaction.
No retained account, schema migration, membership or historical profile is altered.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.security import get_password_hash
from app.db.models.client import Client
from app.db.models.user import User


async def create_public_client_account(
    *,
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> User:
    """Persist one CLIENT account and personal profile atomically.

    The schema already validates and normalizes a two-part name. Split at the
    last whitespace to preserve compound given names without fake surnames.
    """
    first_name, last_name = full_name.rsplit(" ", 1)
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        role=UserRole.client,
    )
    client = Client(first_name=first_name, last_name=last_name, user=user)
    db.add(client)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(user)
    return user

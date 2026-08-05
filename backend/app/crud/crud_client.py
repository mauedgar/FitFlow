"""CRUD para Client (asíncrono, Sprint 6-7).

----------------------------------------
• Perfil de cliente asociado a Person.
• Métodos auxiliares: búsqueda por user_id, creación ligada a User.
• Carga selectiva de relaciones (bookings, membership, user).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Client, Membership, User
from app.schemas.client import ClientCreate, ClientUpdate

from .base import CRUDBase

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    """CRUD especializado para perfiles de cliente."""

    # ------------------------------------------------------------------ #
    # Búsquedas específicas
    # ------------------------------------------------------------------ #
    async def get_by_user_id(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        include_relations: bool = False,
    ) -> Client | None:
        """Obtiene un perfil de cliente a partir del ID de un usuario."""
        stmt = select(Client).join(Client.user).where(User.id == user_id)

        if include_relations:
            stmt = stmt.options(
                selectinload(Client.bookings),
                selectinload(Client.membership),
                selectinload(Client.user),
            )

        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_with_relations(
        self,
        db: AsyncSession,
        *,
        client_id: UUID,
    ) -> Client | None:
        """Obtiene un cliente con todas sus relaciones cargadas."""
        stmt = (
            select(Client)
            .where(Client.id == client_id, Client.deleted_at.is_(None))  # type: ignore[attr-defined]
            .options(
                selectinload(Client.bookings),
                selectinload(Client.membership),
                selectinload(Client.user),
            )
        )

        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_by_membership_id(
        self,
        db: AsyncSession,
        *,
        membership_id: UUID,
    ) -> Client | None:
        """Obtiene un cliente a partir del ID de su membresía (útil para auditoría)."""
        stmt = (
            select(Client)
            .join(Client.membership)
            .where(Membership.id == membership_id)
        )

        res = await db.execute(stmt)
        return res.scalars().first()

    # ------------------------------------------------------------------ #
    # Creación asociada a User
    # ------------------------------------------------------------------ #
    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: ClientCreate,
        user: User,
    ) -> Client:
        """Crea un perfil de cliente y lo asocia a un usuario existente."""
        data = obj_in.model_dump()

        db_obj = Client(
            first_name=data["first_name"], # pyright: ignore[reportCallIssue]
            last_name=data["last_name"], # pyright: ignore[reportCallIssue]
            document_number=data.get("document_number"), # pyright: ignore[reportCallIssue]
            address=data.get("address"), # pyright: ignore[reportCallIssue]
            medical_fit_url=data.get("medical_fit_url"), # pyright: ignore[reportCallIssue]
            profile_image_url=data.get("profile_image_url"), # pyright: ignore[reportCallIssue]
            user=user, # pyright: ignore[reportCallIssue]
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instancia reusable
client = CRUDClient(Client)

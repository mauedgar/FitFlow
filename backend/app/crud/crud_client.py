"""
CRUD para Client (asíncrono, Sprint 6–7)
----------------------------------------
• Perfil de cliente asociado a Person.
• Métodos auxiliares: búsqueda por user_id, creación ligada a User.
• Carga selectiva de relaciones (bookings, membership, user).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Client, Membership, User
from app.schemas.client import ClientCreate, ClientUpdate

from .base import CRUDBase


class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
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
        """
        Obtiene un perfil de Cliente a partir del ID de un User.
        """
        stmt = (
            select(Client)
            .join(Client.user)
            .where(User.id == user_id)
        )

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
        """
        Obtiene un cliente con todas sus relaciones cargadas.
        Ideal para:
            • /clients/{id}
            • /clients/me
            • dashboards
        """
        stmt = (
            select(Client)
            .where(Client.id == client_id, Client.deleted_at.is_(None))
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
        """
        Obtiene un cliente a partir del ID de su membresía.
        Útil para auditoría y vistas operativas.
        """
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
        """
        Crea un perfil de Cliente y lo asocia a un User existente.
        """
        data = obj_in.model_dump()

        db_obj = Client(
            first_name=data["first_name"],
            last_name=data["last_name"],
            document_number=data.get("document_number"),
            address=data.get("address"),
            medical_fit_url=data.get("medical_fit_url"),
            profile_image_url=data.get("profile_image_url"),
            user=user,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


client = CRUDClient(Client)

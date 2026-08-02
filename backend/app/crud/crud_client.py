"""
CRUD para Client (asíncrono, Sprint 5)
--------------------------------------
• Perfil de cliente asociado a un User.
• Métodos auxiliares: búsqueda por user_id, creación ligada a User.
"""

from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client, User
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
    ) -> Optional[Client]:
        """
        Obtiene un perfil de Cliente a partir del ID de un User.
        """
        stmt = (
            select(Client)
            .join(Client.user)
            .where(User.id == user_id)
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
        db_obj = Client(
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            passport=obj_in.passport,
            address=obj_in.address,
            medical_fit_url=obj_in.medical_fit_url,
            profile_image_url=obj_in.profile_image_url,
            user=user,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


client = CRUDClient(Client)

"""
CRUD para User (asíncrono, Sprint 6–7)
--------------------------------------
• Gestión de cuentas autenticables.
• Creación con contraseña hasheada.
• Actualización parcial segura.
• Carga selectiva del perfil asociado (Person).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> User | None:
        """
        Obtiene un usuario por su ID, con opción de incluir su perfil Person.
        """
        opts = (
            [
                selectinload(User.person_profile),
            ]
            if include_relations
            else None
        )
        return await super().get(db, id=id, options=opts)

    # ------------------------------------------------------------------ #
    # Búsquedas específicas
    # ------------------------------------------------------------------ #
    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
        include_relations: bool = False,
    ) -> User | None:
        """
        Obtiene un usuario por su email.
        """
        stmt = select(User).where(User.email == email)

        if include_relations:
            stmt = stmt.options(selectinload(User.person_profile))

        res = await db.execute(stmt)
        return res.scalars().first()

    # ------------------------------------------------------------------ #
    # Creación con contraseña hasheada
    # ------------------------------------------------------------------ #
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: UserCreate,
    ) -> User:
        """
        Crea un usuario autenticable con contraseña hasheada.
        """
        data = obj_in.model_dump()

        db_obj = User(
            email=data["email"],
            hashed_password=get_password_hash(data["password"]),
            role=data.get("role"),
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # Actualización parcial segura
    # ------------------------------------------------------------------ #
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate,
    ) -> User:
        """
        Actualiza parcialmente un usuario.
        Si se envía una contraseña nueva, se hashea.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        # Si actualiza contraseña → hashear
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return await super().update(db, db_obj=db_obj, obj_in=update_data)


user = CRUDUser(User)

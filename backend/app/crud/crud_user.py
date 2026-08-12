# pyright: ignore-all
"""CRUD para User (asíncrono, Sprint 6-7).

--------------------------------------
• Gestión de cuentas autenticables.
• Creación con contraseña hasheada.
• Actualización parcial segura.
• Carga selectiva del perfil asociado (Person).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from backend.app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD especializado para usuarios autenticables."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_relations: bool = False,
    ) -> User | None:
        """Obtiene un usuario por ID, con opción de incluir su perfil Person."""
        opts: list[ORMOption] | None = (
            [selectinload(User.person_profile)]
            if include_relations
            else None
        )
        return await super().get(db, obj_id=obj_id, options=opts)

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
        """Obtiene un usuario por su email."""
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
        """Crea un usuario autenticable con contraseña hasheada."""
        data = obj_in.model_dump()

        db_obj = User(
            email=data["email"], # pyright: ignore[reportCallIssue]
            hashed_password=get_password_hash(data["password"]), # pyright: ignore[reportCallIssue]
            role=data.get("role"), # pyright: ignore[reportCallIssue]
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
        """Actualiza parcialmente un usuario. Si cambia la contraseña, se hashea."""
        update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return await super().update(db, db_obj=db_obj, obj_in=update_data)


# Instancia final del CRUD (importar esta en deps y auth_service)
user_crud = CRUDUser(User)

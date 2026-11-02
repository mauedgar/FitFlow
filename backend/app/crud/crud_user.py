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

from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:

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
        obj_id: object,
        include_relations: bool = False,
        options: list[ORMOption] | None = None,
    ) -> User | None:
        """Obtiene un usuario por ID, con opción de incluir su perfil Person."""
        opts: list[ORMOption] | None = (
            [selectinload(User.person_profile)]
            if include_relations
            else None
        )
        if options:
            opts = [*(opts or []), *options]
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
        include_deleted: bool = False,
    ) -> User | None:
        """Look up by email; registration can opt into checking reserved deleted emails."""
        stmt = select(User).where(User.email == email)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))

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
        obj_in: UserUpdate | dict[str, object],
    ) -> User:
        """Actualiza parcialmente un usuario. Si cambia la contraseña, se hashea."""
        update_data = dict(obj_in) if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        if "password" in update_data:
            password = update_data.pop("password")
            if not isinstance(password, str):
                raise ValueError("password must be a string")
            update_data["hashed_password"] = get_password_hash(password)

        return await super().update(db, db_obj=db_obj, obj_in=update_data)


# Instancia reusable del CRUD de usuarios.
user = CRUDUser(User)

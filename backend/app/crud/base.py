"""CRUDBase genérico (asíncrono).

Proporciona operaciones básicas de lectura, creación, actualización y eliminación
para modelos SQLAlchemy con soporte de soft-delete y paginación.

Requisitos:
- SQLAlchemy 2.x
- AsyncSession (sqlalchemy.ext.asyncio.AsyncSession)
- Modelos con columnas: id, deleted_at, active
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select

from app.db.base_class import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Clase base para operaciones CRUD asíncronas."""

    def __init__(self, model: type[ModelType]) -> None:
        """Inicializa el CRUD con el modelo SQLAlchemy asociado."""
        self.model = model

    # ------------------------------------------------------------------ #
    # READ
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: object,
        options: list[ORMOption] | None = None,
    ) -> ModelType | None:
        """Obtiene un registro por ID, ignorando los soft-deleted."""
        stmt = select(self.model).where(
            self.model.id == obj_id, # pyright: ignore[reportAttributeAccessIssue]
            self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
        )

        if options:
            for opt in options:
                stmt = stmt.options(opt)

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, object] | None = None,
        options: list[ORMOption] | None = None,
    ) -> list[ModelType]:
        """Obtiene múltiples registros con paginación y filtros dinámicos."""
        stmt = select(self.model).where(
            self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
        )

        if filters:
            for attr, value in filters.items():
                if value is None:
                    continue

                column = getattr(self.model, attr)

                if isinstance(value, list):
                    stmt = stmt.where(column.in_(value))
                else:
                    stmt = stmt.where(column == value)

        if options:
            for opt in options:
                stmt = stmt.options(opt)

        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().unique().all())

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """Crea un nuevo registro en la base de datos."""
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, object],
    ) -> ModelType:
        """Actualiza un registro existente."""
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # DELETE (soft por defecto)
    # ------------------------------------------------------------------ #
    async def remove(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        hard: bool = False,
    ) -> None:
        """Elimina un registro (soft-delete por defecto)."""
        if hard:
            await db.delete(db_obj)
        else:
            db_obj.active = False  # type: ignore[attr-defined]
            db_obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
            db.add(db_obj)

        await db.commit()
        await db.refresh(db_obj)

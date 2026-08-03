"""
CRUDBase genérico (asíncrono)
=============================

• Funciones:
    – get            (por id, ignora soft-deleted)
    – get_multi      (paginación + filtros dinámicos)
    – create
    – update
    – remove         (soft-delete por defecto; hard=True para borrado físico)

• Requisitos:
    – SQLAlchemy 2.x
    – AsyncSession (sqlalchemy.ext.asyncio.AsyncSession)
    – Modelos con columnas: id, deleted_at, active
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    # ------------------------------------------------------------------ #
    # READ
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: Any,
        options: None | list[Any] = None,
    ) -> None | ModelType:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),  # solo registros activos
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
        filters: None | dict[str, Any] = None,
        options: None | list[Any] = None,
    ) -> list[ModelType]:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        # filtros simples de igualdad / IN
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
        return res.scalars().unique().all()

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
    ) -> ModelType:
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
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # DELETE  (soft por defecto)
    # ------------------------------------------------------------------ #
    async def remove(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        hard: bool = False,
    ) -> None:
        if hard:
            await db.delete(db_obj)
        else:
            db_obj.active = False
            db_obj.deleted_at = datetime.now(timezone.utc)
            db.add(db_obj)
        await db.commit()
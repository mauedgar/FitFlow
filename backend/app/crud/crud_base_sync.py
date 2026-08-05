"""CRUDSync genérico (sincrónico).

Versión sincrónica del CRUDBase asíncrono, pensada para:

• Scripts administrativos
• Workers sin async
• Migraciones manuales
• Herramientas internas
• Pruebas unitarias sin AsyncSession

Requisitos:
    * SQLAlchemy ORM (Session)
    * Modelos con columnas: id, deleted_at, active
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# --------------------------------------------------------------------------- #
# Protocol para que Pylance valide atributos dinámicos de SQLAlchemy
# --------------------------------------------------------------------------- #
class ModelProtocol(Protocol):
    """id dinamico."""

    id: Any
    deleted_at: Any
    active: bool


ModelType = TypeVar("ModelType", bound=ModelProtocol)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDSync(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Clase base para operaciones CRUD sincrónicas."""

    def __init__(self, model: type[ModelType]) -> None:
        """No se."""
        self.model = model

    # ------------------------------------------------------------------ #
    # READ
    # ------------------------------------------------------------------ #
    def get(self, db: Session, *, obj_id: object) -> ModelType | None:
        """Obtiene un registro por ID, ignorando soft-deleted."""
        return (
            db.query(self.model)
            .filter(
                self.model.id == obj_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, object] | None = None,
    ) -> list[ModelType]:
        """Obtiene múltiples registros con paginación y filtros dinámicos."""
        query = db.query(self.model).filter(self.model.deleted_at.is_(None))

        if filters:
            for attr, value in filters.items():
                if value is None:
                    continue

                column = getattr(self.model, attr)

                if isinstance(value, list):
                    query = query.filter(column.in_(value))
                else:
                    query = query.filter(column == value)

        return query.offset(skip).limit(limit).all()

    # ------------------------------------------------------------------ #
    # CREATE
    # ------------------------------------------------------------------ #
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Crea un nuevo registro en la base de datos."""
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, object],
    ) -> ModelType:
        """Actualiza un registro existente."""
        data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        for field, value in data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ------------------------------------------------------------------ #
    # DELETE (soft por defecto)
    # ------------------------------------------------------------------ #
    def remove(self, db: Session, *, db_obj: ModelType, hard: bool = False) -> None:
        """Elimina un registro (soft-delete por defecto)."""
        if hard:
            db.delete(db_obj)
        else:
            db_obj.active = False
            db_obj.deleted_at = datetime.now(timezone.utc)
            db.add(db_obj)

        db.commit()

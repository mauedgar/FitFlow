"""
CRUD para Teacher (asíncrono, Sprint 6–7)
-----------------------------------------
• Perfil de profesor asociado a Person.
• Búsquedas específicas.
• Carga selectiva de relaciones (class_schedules).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# IMPORTS CORRECTOS (evitan el error de Pylance)
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.teacher import TeacherCreate, TeacherUpdate

from .base import CRUDBase


class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_relations: bool = False,
    ) -> Teacher | None:
        """
        Obtiene un profesor por su ID, con opción de incluir relaciones.
        """
        opts = (
            [
                selectinload(Teacher.class_schedules),
            ]
            if include_relations
            else None
        )
        return await super().get(db, id=id, options=opts)

    # ------------------------------------------------------------------ #
    # Búsquedas específicas
    # ------------------------------------------------------------------ #
    async def get_by_full_name(
        self,
        db: AsyncSession,
        *,
        full_name: str,
    ) -> Teacher | None:
        """
        Obtiene un profesor por su nombre completo (búsqueda flexible).
        """
        normalized = f"%{full_name.strip().lower()}%"

        stmt = (
            select(Teacher)
            .where(
                func.lower(Teacher.first_name + " " + Teacher.last_name).like(normalized)
            )
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
        obj_in: TeacherCreate,
        user: User,
    ) -> Teacher:
        """
        Crea un perfil de Profesor y lo asocia a un User existente.
        """
        data = obj_in.model_dump()

        db_obj = Teacher(
            first_name=data["first_name"],
            last_name=data["last_name"],
            document_number=data.get("document_number"),
            address=data.get("address"),
            medical_fit_url=data.get("medical_fit_url"),
            profile_image_url=data.get("profile_image_url"),
            bio=data.get("bio"),
            cuil=data.get("cuil"),
            user=user,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


teacher = CRUDTeacher(Teacher)

"""
CRUD para Teacher (asíncrono, Sprint 5)
---------------------------------------
• Perfil de profesor asociado a un User.
• Métodos auxiliares: búsqueda por nombre completo, creación ligada a User.
"""

from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Teacher, User
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from .base import CRUDBase


class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    # ------------------------------------------------------------------ #
    # Búsquedas específicas
    # ------------------------------------------------------------------ #
    async def get_by_full_name(
        self,
        db: AsyncSession,
        *,
        full_name: str,
    ) -> Optional[Teacher]:
        """
        Obtiene un profesor por su nombre completo.
        """
        stmt = select(Teacher).where(Teacher.full_name == full_name)
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
        db_obj = Teacher(
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            passport=obj_in.passport,
            address=obj_in.address,
            bio=obj_in.bio,
            cuil=obj_in.cuil,
            user=user,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


teacher = CRUDTeacher(Teacher)

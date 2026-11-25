# pyright: ignore-all
"""CRUD para Teacher (asíncrono, Sprint 6-7).

-----------------------------------------
• Perfil de profesor asociado a Person.
• Búsquedas específicas.
• Carga selectiva de relaciones (class_schedules).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.db.models.class_schedule import ClassSchedule
from app.db.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm.interfaces import ORMOption

    from app.db.models.user import User

class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    """CRUD especializado para perfiles de profesor."""

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    async def get(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        include_relations: bool = False,
    ) -> Teacher | None:
        """Obtiene un profesor por ID, con opción de incluir relaciones."""
        opts: list[ORMOption] | None = (
            [selectinload(Teacher.class_schedules)]
            if include_relations
            else None
        )
        return await super().get(db, obj_id=obj_id, options=opts)

    async def get_private(
        self,
        db: AsyncSession,
        *,
        obj_id: UUID,
        owner_user_id: UUID | None,
    ) -> Teacher | None:
        """Select the exact profile and, for self access, its persisted owner."""
        stmt = select(Teacher).where(
            Teacher.id == obj_id,
            Teacher.deleted_at.is_(None),
        )
        if owner_user_id is not None:
            stmt = stmt.where(Teacher.user_id == owner_user_id)
        stmt = stmt.options(
            selectinload(Teacher.class_schedules).selectinload(ClassSchedule.gym_class),
            selectinload(Teacher.class_schedules).selectinload(ClassSchedule.teacher),
        ).execution_options(populate_existing=True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------ #
    # Búsquedas específicas
    # ------------------------------------------------------------------ #
    async def get_by_full_name(
        self,
        db: AsyncSession,
        *,
        full_name: str,
    ) -> Teacher | None:
        """Obtiene un profesor por su nombre completo (búsqueda flexible)."""
        normalized = f"%{full_name.strip().lower()}%"

        stmt = select(Teacher).where(
            func.lower(Teacher.first_name + " " + Teacher.last_name).like(normalized),
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
        """Crea un perfil de profesor y lo asocia a un usuario existente."""
        data = obj_in.model_dump()

        db_obj = Teacher(
            first_name=data["first_name"], #pyright: ignore[reportCallIssue]
            last_name=data["last_name"], #pyright: ignore[reportCallIssue]
            document_number=data.get("document_number"), #pyright: ignore[reportCallIssue]
            address=data.get("address"), #pyright: ignore[reportCallIssue]
            medical_fit_url=data.get("medical_fit_url"), #pyright: ignore[reportCallIssue]
            profile_image_url=data.get("profile_image_url"), #pyright: ignore[reportCallIssue]
            bio=data.get("bio"), #pyright: ignore[reportCallIssue]
            cuil=data.get("cuil"), #pyright: ignore[reportCallIssue]
            user=user, #pyright: ignore[reportCallIssue]
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


teacher = CRUDTeacher(Teacher)

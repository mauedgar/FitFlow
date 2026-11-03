"""Dependencias y Guards de Autorización (Enterprise).

--------------------------------------------------
• Validación de JWT
• Validación de usuario activo
• Guards por rol
• Guards combinados (operativo, público autenticado)
• Guards admin/self
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import decode_token, is_access_token_payload
from app.crud.crud_user import user as user_crud
from app.db.models.teacher import Teacher
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.token import TokenPayload
from app.schemas.user import UserPublic
from app.services.auth_service import get_user_from_token
from app.services.errors import AuthError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


# --------------------------------------------------------------------------- #
# OAuth2 / JWT
# --------------------------------------------------------------------------- #

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Valida el JWT, obtiene el usuario y verifica que esté activo."""
    payload = decode_token(token)
    # An untyped JWT may be a legacy refresh token; reject it as Bearer.
    if payload is None or not is_access_token_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = TokenPayload(**payload)
    except ValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mal formado",
        ) from err

    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin sujeto válido",
        )

    try:
        user_id = UUID(token_data.sub)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mal formado",
        ) from err

    user = await user_crud.get(db, obj_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.active:  # type: ignore[reportGeneralTypeIssues]
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return user


# --------------------------------------------------------------------------- #
# require_current_user (versión normalizada)
# --------------------------------------------------------------------------- #

async def require_current_user(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserPublic:
    """Devuelve el usuario autenticado usando el servicio de Auth."""
    try:
        return await get_user_from_token(token, db)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc



# --------------------------------------------------------------------------- #
# Role-based guards
# --------------------------------------------------------------------------- #

def require_roles(*allowed_roles: UserRole) -> Callable[..., Awaitable[UserPublic]]:
    """Valida que el usuario tenga alguno de los roles permitidos."""
    async def guard(user: Annotated[UserPublic, Depends(require_current_user)]) -> UserPublic:
        if user.role not in allowed_roles:
            roles_list = ", ".join(r.value for r in allowed_roles)
            msg = f"Este recurso requiere uno de los siguientes roles: {roles_list}."
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=msg,
            )
        return user

    return guard


# --------------------------------------------------------------------------- #
# Admin or Self
# --------------------------------------------------------------------------- #

def require_admin_or_self(id_param_name: str = "user_id") -> Callable[..., Awaitable[UserPublic]]:
    """Permite acceso si el usuario es admin o si el recurso pertenece al propio usuario."""
    async def guard(
        request: Request,
        user: Annotated[UserPublic, Depends(require_current_user)],
    ) -> UserPublic:
        if user.role == UserRole.admin:
            return user

        requested_id = (
            request.path_params.get(id_param_name)
            or request.query_params.get(id_param_name)
        )

        if requested_id and str(user.id) == str(requested_id):
            return user

        msg = "Acceso denegado."
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    return guard


# --------------------------------------------------------------------------- #
# Aliases shortcuts
# --------------------------------------------------------------------------- #

require_admin = require_roles(UserRole.admin)
require_front_desk = require_roles(UserRole.front_desk)
require_teacher = require_roles(UserRole.teacher)
require_client = require_roles(UserRole.client)

require_admin_or_front_desk = require_roles(UserRole.admin, UserRole.front_desk)
require_admin_or_teacher = require_roles(UserRole.admin, UserRole.teacher)
require_admin_or_client = require_roles(UserRole.admin, UserRole.client)

require_admin_or_self_guard = require_admin_or_self("user_id")
require_admin_client_or_self = require_admin_or_self("client_id")
async def require_admin_teacher_or_self(
    teacher_id: UUID,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[UserPublic, Depends(require_current_user)],
) -> UserPublic:
    """Admin or owner of the Teacher profile, using Person.user_id (not profile id).

    The path contains a Teacher/Person UUID while the JWT subject identifies
    the User account UUID. Resolve ownership through the persisted relationship.
    """
    if current_user.role == UserRole.admin:
        return current_user
    if current_user.role != UserRole.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.",
        )
    profile = await db.scalar(
        select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.deleted_at.is_(None),
        )
    )
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.",
        )
    return current_user

require_operational = require_roles(
    UserRole.admin,
    UserRole.teacher,
    UserRole.front_desk,
)

require_any_role = require_roles(
    UserRole.admin,
    UserRole.teacher,
    UserRole.client,
    UserRole.front_desk,
)

"""Dependencias y Guards de Autorización (Enterprise).

--------------------------------------------------
• Validación de JWT
• Validación de usuario activo
• Guards por rol
• Guards combinados (operativo, público autenticado)
• Guards admin/self
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import decode_token
from app.crud.crud_user import user_crud
from app.db.session import get_async_session
from app.schemas.token import TokenPayload
from app.schemas.user import UserPublic  # noqa: TC001
from app.services.auth_service import get_user_from_token
from app.services.errors import AuthError, PermissionDeniedError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User


# --------------------------------------------------------------------------- #
# OAuth2 / JWT
# --------------------------------------------------------------------------- #

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
)


async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Valida el JWT, obtiene el usuario y verifica que esté activo."""
    payload = decode_token(token)
    if payload is None:
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

    user = await user_crud.get_by_email(db, email=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.active:  # type: ignore[reportGeneralTypeIssues]
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return user


# --------------------------------------------------------------------------- #
# require_current_user (versión normalizada)
# --------------------------------------------------------------------------- #

async def require_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
) -> UserPublic:
    """Devuelve el usuario autenticado usando el servicio de Auth."""
    user = await get_user_from_token(token, db)
    if user is None:
        msg = "Token inválido o ausente."
        raise AuthError(msg)
    return user



# --------------------------------------------------------------------------- #
# Role-based guards
# --------------------------------------------------------------------------- #

def require_roles(*allowed_roles: UserRole) -> Callable[..., Awaitable[UserPublic]]:
    """Valida que el usuario tenga alguno de los roles permitidos."""
    async def guard(user: UserPublic = Depends(require_current_user)) -> UserPublic:
        if user.role not in allowed_roles:
            roles_list = ", ".join(r.value for r in allowed_roles)
            msg = f"Este recurso requiere uno de los siguientes roles: {roles_list}."
            raise PermissionDeniedError(
                msg,
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
        user: UserPublic = Depends(require_current_user),
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
        raise PermissionDeniedError(msg)

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
require_admin_teacher_or_self = require_admin_or_self("teacher_id")

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

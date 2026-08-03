"""
Dependencias y Guards de Autorización (Sprint 6–7)
--------------------------------------------------
• Validación de JWT
• Validación de usuario activo
• Guards por rol
• Guards combinados (operativo, público autenticado)
• Guards admin/self
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.db.session import get_async_session
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload

# ruff: noqa: B008

# --------------------------------------------------------------------------- #
# OAuth2 / JWT
# --------------------------------------------------------------------------- #

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/token")


async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Valida el JWT, obtiene el usuario y verifica que esté activo.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await crud.user.get_by_email(db, email=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return user


# --------------------------------------------------------------------------- #
# Role-based guards
# --------------------------------------------------------------------------- #

def require_roles(*allowed_roles: UserRole):
    """
    Valida que el usuario tenga alguno de los roles permitidos.
    Mensajes profesionales y específicos.
    """

    role_messages = {
        UserRole.admin: "Se requieren permisos de administrador.",
        UserRole.front_desk: "Se requieren permisos de recepción.",
        UserRole.teacher: "Se requieren permisos de profesor.",
        UserRole.client: "Se requieren permisos de cliente.",
    }

    async def guard(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            if len(allowed_roles) == 1:
                msg = role_messages.get(allowed_roles[0], "Permisos insuficientes.")
            else:
                roles_list = ", ".join(r.value for r in allowed_roles)
                msg = f"Este recurso requiere uno de los siguientes roles: {roles_list}."

            raise HTTPException(status_code=403, detail=msg)

        return user

    return guard


# --------------------------------------------------------------------------- #
# Admin or Self
# --------------------------------------------------------------------------- #

def require_admin_or_self(id_param_name: str = "user_id"):
    """
    Permite acceso si el usuario es admin o si el recurso pertenece al propio usuario.
    """
    async def guard(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        if user.role == UserRole.admin:
            return user

        requested_id = (
            request.path_params.get(id_param_name)
            or request.query_params.get(id_param_name)
        )

        if requested_id and str(user.id) == str(requested_id):
            return user

        raise HTTPException(status_code=403, detail="Acceso denegado")

    return guard


# --------------------------------------------------------------------------- #
# Aliases (shortcuts)
# --------------------------------------------------------------------------- #

require_admin = require_roles(UserRole.admin)
require_front_desk = require_roles(UserRole.front_desk)
require_teacher = require_roles(UserRole.teacher)
require_client = require_roles(UserRole.client)

# Combinados
require_admin_or_front_desk = require_roles(UserRole.admin, UserRole.front_desk)
require_admin_or_teacher = require_roles(UserRole.admin, UserRole.teacher)
require_admin_or_client = require_roles(UserRole.admin, UserRole.client)

# Self
require_admin_or_self_guard = require_admin_or_self("user_id")
require_admin_client_or_self = require_admin_or_self("client_id")
require_admin_teacher_or_self = require_admin_or_self("teacher_id")

# Nuevo: Operativo (admin + teacher + front_desk)
require_operational = require_roles(
    UserRole.admin,
    UserRole.teacher,
    UserRole.front_desk,
)

# Nuevo: Público autenticado (cualquier rol)
require_any_role = require_roles(
    UserRole.admin,
    UserRole.teacher,
    UserRole.client,
    UserRole.front_desk,
)

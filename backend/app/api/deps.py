from __future__ import annotations

from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.db.session import get_async_session
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload


# --------------------------------------------------------------------------- #
# OAuth2 / JWT
# --------------------------------------------------------------------------- #
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/token")


async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Valida el JWT, obtiene el usuario y verifica que exista.
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return user


# --------------------------------------------------------------------------- #
# Active user guard
# --------------------------------------------------------------------------- #
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user


# --------------------------------------------------------------------------- #
# Role-based guards
# --------------------------------------------------------------------------- #
async def get_current_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
    return user


async def get_current_teacher(
    user: User = Depends(get_current_active_user),
) -> User:
    if user.role != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol teacher")
    return user


async def get_current_client(
    user: User = Depends(get_current_active_user),
) -> User:
    if user.role != UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol client")
    return user


# --------------------------------------------------------------------------- #
# Guard: admin o el propio usuario/cliente
# --------------------------------------------------------------------------- #
async def get_admin_or_self(
    user: User = Depends(get_current_active_user),
    requested_id: UUID | None = None,  # normalmente extraído de path o query param
) -> User:
    """
    Permite acceso si el usuario autenticado es admin o si el `requested_id`
    coincide con su propio Person.id (o User.id según tu lógica).
    """
    if user.role == UserRole.admin:
        return user

    if requested_id and user.person_profile and user.person_profile.id == requested_id:
        return user

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
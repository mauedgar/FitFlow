# app/services/auth_service.py
"""Servicio de autenticación: decodifica token y devuelve UserPublic."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.security import decode_token, is_access_token_payload
from app.core.session_revocation import is_access_credential_revoked
from app.crud.crud_user import user as user_crud
from app.db.session import get_async_session
from app.schemas.token import TokenPayload
from app.schemas.user import UserPublic
from app.services.errors import AuthError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import User


async def get_user_from_token(token: str, db: "AsyncSession | None" = None) -> UserPublic:  # noqa: UP037
    """Decodifica JWT y devuelve el usuario público.

    Lanza AuthError en cualquier fallo de autenticación o estado.
    """
    if db is None:
        gen = get_async_session()
        try:
            db = await gen.__anext__()
        except StopAsyncIteration as err:
            msg = "No se pudo obtener sesión de DB."
            raise AuthError(msg) from err

    payload = decode_token(token)
    if payload is None or not is_access_token_payload(payload):
        msg_0 = "Token inválido o expirado."
        raise AuthError(msg_0)

    if is_access_credential_revoked(token, payload):
        raise AuthError("Sesión revocada.")

    try:
        token_data = TokenPayload(**payload)
    except Exception as err:
        msg_1 = "Token mal formado."
        raise AuthError(msg_1) from err

    if token_data.sub is None:
        msg_2 = "Token sin sujeto válido."
        raise AuthError(msg_2)

    try:
        user_id = UUID(token_data.sub)
    except ValueError:
        user = await user_crud.get_by_email(db=db, email=token_data.sub)
    else:
        user = await user_crud.get(db=db, obj_id=user_id)

    if not user:
        msg_3 = "Usuario no encontrado."
        raise AuthError(msg_3)

    if not getattr(user, "active", True):  # type: ignore[reportGeneralTypeIssues]
        msg_4 = "Usuario inactivo."
        raise AuthError(msg_4)

    return UserPublic.model_validate(user)

async def get_active_user_for_refresh(subject: str, db: AsyncSession) -> User | None:
    """Resolve the current persisted account from a registered refresh subject.

    Legacy access-subject email fallback does not apply to refresh tokens. A
    malformed, missing, soft-deleted or disabled account cannot mint access.
    """
    try:
        user_id = UUID(subject)
    except (ValueError, TypeError):
        return None
    user = await user_crud.get(db, obj_id=user_id)
    if user is None or not user.active:
        return None
    return user

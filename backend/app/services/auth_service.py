# app/services/auth_service.py
"""Servicio de autenticación: decodifica token y devuelve UserPublic."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.security import decode_token, is_access_token_payload
from pydantic import ValidationError
from app.crud import auth_session as session_ledger
from app.crud.crud_user import user as user_crud
from app.schemas.token import TokenPayload
from app.schemas.user import UserPublic
from app.services.errors import AuthError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_from_token(token: str, db: "AsyncSession") -> UserPublic:
    """Decodifica JWT y devuelve el usuario público.

    Lanza AuthError en cualquier fallo de autenticación o estado.
    """
    # The caller owns the injected AsyncSession lifetime. No orphaned async
    # generator or implicit connection survives success/failure here.
    if db is None:
        raise AuthError("Sesión de DB requerida.")

    payload = decode_token(token)
    if payload is None or not is_access_token_payload(payload):
        msg_0 = "Token inválido o expirado."
        raise AuthError(msg_0)

    try:
        token_data = TokenPayload(**payload)
    except ValidationError as err:
        msg_1 = "Token mal formado."
        raise AuthError(msg_1) from err

    if token_data.sub is None:
        msg_2 = "Token sin sujeto válido."
        raise AuthError(msg_2)

    # A signed access without a registered SID can no longer resolve any
    # user, including old email subjects and otherwise valid legacy JWTs.
    try:
        user_id = UUID(token_data.sub)
    except ValueError as exc:
        raise AuthError("Token mal formado.") from exc
    if not await session_ledger.is_active(
        db, sid=payload["sid"], subject=token_data.sub,
    ):
        raise AuthError("Sesión no registrada o revocada.")
    user = await user_crud.get(db=db, obj_id=user_id)
    if not user:
        msg_3 = "Usuario no encontrado."
        raise AuthError(msg_3)

    if not getattr(user, "active", True):  # type: ignore[reportGeneralTypeIssues]
        msg_4 = "Usuario inactivo."
        raise AuthError(msg_4)

    if getattr(user, "deleted_at", None) is not None:
        raise AuthError("Usuario eliminado.")
    return UserPublic.model_validate(user)
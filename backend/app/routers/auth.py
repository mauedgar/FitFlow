"""Router Auth (Sprint 6-7).

• Login con Access + Refresh Tokens
• Refresh de Access Token
• Logout con blacklist + Redis
• Información del usuario autenticado
• Integrado con CRUDUser y servicios
• Compatible con TanStack Query
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.blacklist import blacklist_token, is_token_blacklisted
from app.core.deps import get_current_user
from app.core.token_store import (
    delete_refresh_token,
    is_refresh_token_valid,
    store_refresh_token,
)
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.token import Token, TokenPair
from app.schemas.user import UserPublic
from app.services.errors import ExternalServiceError
from app.services.user_service import get_by_email as user_get_by_email, to_user_public

logger = logging.getLogger("fitflow.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=TokenPair, status_code=status.HTTP_200_OK)
async def login_for_tokens(
    *,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenPair:
    """Autentica al usuario y devuelve Access + Refresh Tokens."""
    try:
        user = await user_get_by_email(db=db, email=form_data.username)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("DB error on get_by_email during login")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if not user or not security.verify_password(form_data.password, user.hashed_password):  # pyright: ignore[reportArgumentType]
        logger.warning("Failed login attempt for email=%s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = security.create_refresh_token(data={"sub": str(user.id)})

    try:
        store_refresh_token(str(user.id), refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to store refresh token for user_id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    logger.info("User %s logged in successfully", user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    *,
    refresh_token: str,
) -> Token:
    """Renueva el Access Token usando un Refresh Token válido."""
    try:
        blacklisted = is_token_blacklisted(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if blacklisted:
        logger.warning("Attempt to refresh with blacklisted token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalidado.")

    payload = security.decode_token(refresh_token)
    if payload is None or "sub" not in payload:
        logger.warning("Invalid or expired refresh token provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado.")

    try:
        registered = is_refresh_token_valid(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if not registered:
        logger.warning("Refresh token not registered in store")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token no registrado.")

    access_token = security.create_access_token(data={"sub": payload["sub"]})
    logger.info("Access token refreshed for user_id=%s", payload.get("sub"))
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def logout(
    *,
    refresh_token: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Logout real: invalida refresh token en Redis + blacklist.

    Requiere autenticación para evitar invalidaciones arbitrarias.
    """
    payload = security.decode_token(refresh_token)
    if payload is None or "sub" not in payload:
        logger.warning("Logout attempted with invalid refresh token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token inválido.")

    if str(current_user.id) != str(payload["sub"]):
        logger.warning("User %s attempted to logout token of user %s", current_user.id, payload.get("sub"))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para invalidar este token.")

    try:
        delete_refresh_token(refresh_token)
        blacklist_token(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error invalidating refresh token for user=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    # 204 No Content implícito


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def get_me(
    *,
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    """Devuelve información del usuario autenticado."""
    try:
        return to_user_public(current_user)
    except Exception as exc:
        logger.exception("Error converting user to public for user=%s", getattr(current_user, "id", None))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

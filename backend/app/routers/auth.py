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
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.blacklist import is_token_blacklisted
from app.core.deps import get_current_user
from app.core.session_revocation import commit_logout, is_session_revoked, session_ids_match
from app.services.auth_service import get_active_user_for_refresh
from app.core.token_store import (
    is_refresh_token_valid,
    store_refresh_token,
)
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.token import RefreshTokenRequest, Token, TokenPair
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

    if not user or not security.verify_password(form_data.password, user.hashed_password) or not user.active:  # pyright: ignore[reportArgumentType]
        logger.warning("Failed login attempt for email=%s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session_id = str(uuid4())
    access_token = security.create_access_token(data={"sub": str(user.id), "role": user.role.value, "sid": session_id})
    refresh_token = security.create_refresh_token(data={"sub": str(user.id), "sid": session_id})

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
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Renueva el Access Token usando un Refresh Token válido."""
    refresh_token = token_request.refresh_token
    try:
        blacklisted = is_token_blacklisted(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if blacklisted:
        logger.warning("Attempt to refresh with blacklisted token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalidado.")

    payload = security.decode_token(refresh_token)
    if not security.is_refresh_token_payload(payload):
        logger.warning("Invalid or expired refresh token provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado.")

    if "sid" in payload:
        try:
            revoked_session = is_session_revoked(payload["sid"])
        except ExternalServiceError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        if revoked_session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión revocada.")

    try:
        registered = is_refresh_token_valid(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if not registered:
        logger.warning("Refresh token not registered in store")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token no registrado.")

    # Redis registration alone does not attest that this account still exists,
    # remains active or retains its old role. Load current persisted authority.
    try:
        user = await get_active_user_for_refresh(payload["sub"], db)
    except Exception as exc:
        logger.exception("User lookup failed during token refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno",
        ) from exc
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        )

    access_token = security.create_access_token(
        data={**{"sub": str(user.id), "role": user.role.value}, **({"sid": payload["sid"]} if "sid" in payload else {})}
    )
    logger.info("Access token refreshed for user_id=%s", user.id)
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def logout(
    *,
    token_request: RefreshTokenRequest,
    request: Request,
) -> None:
    """Revoca únicamente la sesión poseída mediante un refresh firmado/registrado.

    Un access expirado no puede bloquear su propia revocación. Un access VÁLIDO
    de una sesión diferente nunca autoriza revocar otra sesión.
    """
    refresh_token = token_request.refresh_token
    payload = security.decode_token(refresh_token)
    if not security.is_refresh_token_payload(payload):
        logger.warning("Logout attempted with invalid refresh token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token inválido.")

    bearer = request.headers.get("authorization", "")
    access_token = bearer[7:] if bearer.lower().startswith("bearer ") else None
    access_payload = security.decode_token(access_token) if access_token else None

    # If the bearer is still valid, it must belong to the exact same user and
    # session. If it is expired, the independently authenticated refresh alone
    # permits its own revocation (never an arbitrary target session).
    if access_payload is not None and (
        not security.is_access_token_payload(access_payload)
        or access_payload.get("sub") != payload["sub"]
        or not session_ids_match(access_payload, payload)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sesión no coincide con el token de refresco.",
        )

    try:
        confirmed = commit_logout(
            refresh_token,
            sid=payload.get("sid"),
            access_token=access_token if access_payload is not None else None,
            subject=payload["sub"],
        )
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error invalidating refresh token for subject=%s", payload["sub"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no registrado o revocado.",
        )

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

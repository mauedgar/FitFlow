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
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core import security, browser_session
from app.core.blacklist import blacklist_token, is_token_blacklisted
from app.core.deps import get_current_user
from app.crud.crud_user import user as user_crud
from app.crud import auth_session as session_ledger
from app.core.token_store import (
    delete_refresh_token,
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

    if (
        user is None
        or not user.active
        or user.deleted_at is not None
        or not security.verify_password(form_data.password, user.hashed_password)
    ):
        logger.warning("Failed login attempt for email=%s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # All new API logins use durable session families. Old signed SID-less
    # credentials remain readable only until their original expiration.
    sid = str(uuid4())
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "sid": sid}
    )
    refresh_token = security.create_refresh_token(
        data={"sub": str(user.id), "sid": sid}
    )
    try:
        await session_ledger.register(
            db, subject=user.id, refresh_token=refresh_token,
        )
    except Exception as exc:
        logger.exception("Durable API login registration not confirmed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistencia de sesiones no disponible.",
        ) from exc

    logger.info("User %s logged in with durable session", user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    *,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Modern signed SID routes to PostgreSQL; SID-less legacy uses Redis."""
    refresh_token = token_request.refresh_token
    signed_payload = security.decode_token(refresh_token)
    if isinstance(signed_payload, dict) and "sid" in signed_payload:
        if not security.is_refresh_token_payload(signed_payload):
            raise HTTPException(status_code=401, detail="Refresh moderno inválido.")
        return await refresh_durable_session(token_request=token_request, db=db)
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

    try:
        registered = is_refresh_token_valid(refresh_token)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    if not registered:
        logger.warning("Refresh token not registered in store")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token no registrado.")

    # Refresh claims never authorize a role. Load current persisted authority.
    try:
        user_id = UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        ) from exc
    try:
        user = await user_crud.get(db, obj_id=user_id)
    except Exception as exc:
        logger.exception("DB error during refresh subject validation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno"
        ) from exc
    if user is None or not user.active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        )
    # Legacy refresh must never extend access beyond its signed expiry.
    legacy_expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    if legacy_expires_at <= datetime.now(tz=UTC):
        raise HTTPException(status_code=401, detail="Refresh legado expirado.")
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_at=legacy_expires_at,
    )
    logger.info("Legacy access issued with bounded expiry for user_id=%s", payload.get("sub"))
    return Token(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def logout(
    *,
    token_request: RefreshTokenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Modern SID logout is durable; original SID-less logout uses Redis.

    Requiere autenticación para evitar invalidaciones arbitrarias.
    """
    refresh_token = token_request.refresh_token
    payload = security.decode_token(refresh_token)
    if not security.is_refresh_token_payload(payload):
        logger.warning("Logout attempted with invalid refresh token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token inválido.")

    if str(current_user.id) != str(payload["sub"]):
        logger.warning("User %s attempted to logout token of user %s", current_user.id, payload.get("sub"))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para invalidar este token.")
    if "sid" in payload:
        await logout_durable_session(token_request=token_request, db=db)
        return

    try:
        if not is_refresh_token_valid(refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token no registrado.",
            )
        delete_refresh_token(refresh_token)
        blacklist_token(refresh_token)
    except HTTPException:
        raise
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


# ---------------------------------------------------------------------------
# Durable modern sessions (opt-in API; legacy routes remain unchanged).
# These endpoints use PostgreSQL as the only revocation authority.
# ---------------------------------------------------------------------------

@router.post("/session/token", response_model=TokenPair, status_code=status.HTTP_200_OK)
async def create_durable_login(
    *,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenPair:
    """Create a modern signed family only after its PostgreSQL COMMIT succeeds."""
    try:
        user = await user_get_by_email(db=db, email=form_data.username)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Persistencia de sesiones no disponible.") from exc
    if (
        user is None
        or not user.active
        or user.deleted_at is not None
        or not security.verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=401, detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    family_id = str(uuid4())
    access_token = security.create_access_token(
        {"sub": str(user.id), "role": user.role.value, "sid": family_id}
    )
    refresh_token = security.create_refresh_token(
        {"sub": str(user.id), "sid": family_id}
    )
    try:
        await session_ledger.register(
            db, subject=user.id, refresh_token=refresh_token
        )
    except Exception as exc:
        logger.exception("Durable login registration could not be confirmed")
        raise HTTPException(
            status_code=503, detail="Persistencia de sesiones no disponible."
        ) from exc
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/session/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_durable_session(
    *,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Mint access only from a still-active, exact signed PostgreSQL family."""
    refresh_token = token_request.refresh_token
    payload = security.decode_token(refresh_token)
    if not security.is_refresh_token_payload(payload) or "sid" not in payload:
        raise HTTPException(status_code=401, detail="Refresh de sesión inválido.")
    try:
        allowed = await session_ledger.is_active(
            db, sid=payload["sid"], subject=payload["sub"],
            refresh_token=refresh_token,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="Persistencia de sesiones no disponible."
        ) from exc
    if not allowed:
        raise HTTPException(status_code=401, detail="Sesión no registrada o revocada.")

    try:
        uid = UUID(payload["sub"])
        user = await user_crud.get(db, obj_id=uid)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Refresh de sesión inválido.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503, detail="Persistencia de sesiones no disponible."
        ) from exc
    if user is None or not user.active or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Usuario inactivo o eliminado.")
    access_token = security.create_access_token(
        {"sub": str(user.id), "role": user.role.value, "sid": payload["sid"]}
    )
    return Token(access_token=access_token)


@router.post("/session/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_durable_session(
    *,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Proof of possession is the signed registered refresh; no access required.

    An expired or missing access bearer cannot obstruct durable logout.
    The only success receipt is PostgreSQL COMMIT or an exact replay.
    """
    token = token_request.refresh_token
    payload = security.decode_token(token)
    if not security.is_refresh_token_payload(payload):
        raise HTTPException(status_code=400, detail="Refresh de sesión inválido.")
    if "sid" not in payload:
        raise HTTPException(
            status_code=409, detail="Token legado: requiere reautenticación.",
        )
    try:
        outcome = await session_ledger.revoke(db, refresh_token=token)
    except Exception as exc:
        logger.exception("Durable session logout cannot confirm PostgreSQL COMMIT")
        raise HTTPException(
            status_code=503, detail="Revocación durable no confirmada."
        ) from exc
    if outcome not in {"COMMITTED", "ALREADY_COMMITTED"}:
        raise HTTPException(status_code=401, detail="Sesión inexistente o inválida.")


# Browser-cookie flow: never serialize the signed refresh JWT into JS-visible JSON.
# API clients retain the separate /session/* bearer mode until cutover is accepted.

async def _browser_access(
    db: AsyncSession, refresh_token: str,
) -> dict[str, str]:
    """Validate signed purpose, exact session digest and current persisted role."""
    payload = security.decode_token(refresh_token)
    if not security.is_refresh_token_payload(payload) or "sid" not in payload:
        raise HTTPException(status_code=401, detail="Sesión de navegador inválida.")
    try:
        active = await session_ledger.is_active(
            db, sid=payload["sid"], subject=payload["sub"],
            refresh_token=refresh_token,
        )
        if not active:
            raise HTTPException(status_code=401, detail="Sesión revocada o expirada.")
        uid = UUID(payload["sub"])
        user = await user_crud.get(db, obj_id=uid)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Sesión de navegador inválida.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Persistencia de sesiones no disponible.") from exc
    if user is None or not user.active or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Usuario no autorizado.")
    access = security.create_access_token(
        {"sub": str(user.id), "role": user.role.value, "sid": payload["sid"]}
    )
    return {"access_token": access, "token_type": "bearer",
            "csrf_token": browser_session.csrf_value(refresh_token)}


@router.post("/browser/token", status_code=status.HTTP_200_OK)
async def browser_cookie_login(
    *,
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Authenticate, durably COMMIT family, set HttpOnly refresh only."""
    browser_session.require_login_origin(request)
    # Do NOT replace a still-active same-browser session family: doing so
    # would orphan a pending logout refresh proof and make durable ACK false.
    prior_cookie = request.cookies.get(browser_session.COOKIE_NAME)
    if prior_cookie:
        prior_claims = security.decode_token(prior_cookie)
        if security.is_refresh_token_payload(prior_claims) and "sid" in prior_claims:
            try:
                active_family = await session_ledger.is_active(
                    db, sid=prior_claims["sid"], subject=prior_claims["sub"],
                    refresh_token=prior_cookie,
                )
            except Exception as exc:
                logger.exception("Browser family replacement status unknown")
                raise HTTPException(
                    status_code=503, detail="Estado de sesión no confirmado."
                ) from exc
            if active_family:
                raise HTTPException(
                    status_code=409,
                    detail="Cerrá la sesión actual y confirmá su revocación antes de ingresar nuevamente.",
                )
    pair = await create_durable_login(form_data=form_data, db=db)
    browser_session.set_refresh_cookie(response, pair.refresh_token)
    return {
        "access_token": pair.access_token,
        "token_type": "bearer",
        "csrf_token": browser_session.csrf_value(pair.refresh_token),
    }


@router.get("/browser/session", status_code=status.HTTP_200_OK)
async def browser_cookie_rehydrate(
    *,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Read-only boot: a cookie does not itself grant access without PG."""
    token = browser_session.cookie_refresh_token(request)
    body = await _browser_access(db, token)
    response.headers["Cache-Control"] = "no-store"
    return body


@router.post("/browser/refresh", status_code=status.HTTP_200_OK)
async def browser_cookie_refresh(
    *,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, str]:
    """Both strict Origin and HMAC CSRF header required for cookie POST."""
    token = browser_session.cookie_refresh_token(request)
    browser_session.verify_state_change(request, token)
    result = await _browser_access(db, token)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/browser/logout", status_code=status.HTTP_204_NO_CONTENT)
async def browser_cookie_logout(
    *,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Clear HttpOnly cookie only after confirmed DB COMMIT or exact replay."""
    token = browser_session.cookie_refresh_token(request)
    browser_session.verify_state_change(request, token)
    payload = security.decode_token(token)
    if not security.is_refresh_token_payload(payload) or "sid" not in payload:
        raise HTTPException(status_code=401, detail="Sesión de navegador inválida.")
    try:
        outcome = await session_ledger.revoke(db, refresh_token=token)
    except Exception as exc:
        logger.exception("Browser logout PostgreSQL ACK not confirmed")
        raise HTTPException(status_code=503, detail="Logout no confirmado.") from exc
    if outcome not in {"COMMITTED", "ALREADY_COMMITTED"}:
        raise HTTPException(status_code=401, detail="Sesión revocada o inválida.")
    browser_session.clear_refresh_cookie(response)

"""Router Auth (Sprint 6-7).

• Login con Access + Refresh Tokens
• Refresh de Access Token
• Logout y revocación transaccional con PostgreSQL
• Información del usuario autenticado
• Integrado con CRUDUser y servicios
• Compatible con TanStack Query
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core import security, browser_session
from app.core.blacklist import blacklist_token, is_token_blacklisted  # noqa: F401 - old test injection only
from app.core.deps import get_current_user
from app.crud.crud_user import user as user_crud
from app.crud import auth_session as session_ledger
from app.core.token_store import (
    delete_refresh_token,  # noqa: F401 - old test injection only
    is_refresh_token_valid,  # noqa: F401 - old test injection only
    store_refresh_token,  # noqa: F401 - old test injection only
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
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> TokenPair:
    """Autentica al usuario y devuelve Access + Refresh Tokens."""
    try:
        user = await user_get_by_email(db=db, email=form_data.username)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Persistencia de sesiones no disponible.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected get_by_email failure during login")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from exc

    if (
        user is None
        or not user.active
        or user.deleted_at is not None
        or not security.verify_password(form_data.password, user.hashed_password)
    ):
        logger.warning("Failed durable API login authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # All API logins and bearer guards now require a typed, registered SID.
    # Historical SID-less credentials are not accepted, even if signed.
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
    response.headers["Cache-Control"] = "no-store"
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    *,
    response: Response,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Only PostgreSQL-backed SID sessions may refresh; Redis is never read."""
    payload = security.decode_token(token_request.refresh_token)
    if not security.is_modern_refresh_token_payload(payload):
        raise HTTPException(status_code=401, detail="Refresh de sesión inválido.")
    return await refresh_durable_session(
        response=response, token_request=token_request, db=db,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def logout(
    *,
    token_request: RefreshTokenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Only owner-authenticated durable PostgreSQL SID logout is supported."""
    payload = security.decode_token(token_request.refresh_token)
    if not security.is_refresh_token_payload(payload):
        raise HTTPException(status_code=400, detail="Refresh token inválido.")
    if not security.is_modern_refresh_token_payload(payload):
        raise HTTPException(status_code=401, detail="Refresh de sesión inválido.")
    if str(current_user.id) != str(payload["sub"]):
        raise HTTPException(status_code=403, detail="No autorizado para invalidar este token.")
    await logout_durable_session(token_request=token_request, db=db)


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
# Durable modern sessions; original /token, /refresh and /logout are
# PostgreSQL-backed aliases, not Redis-based legacy authority.
# ---------------------------------------------------------------------------

@router.post("/session/token", response_model=TokenPair, status_code=status.HTTP_200_OK)
async def create_durable_login(
    *,
    response: Response,
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
    response.headers["Cache-Control"] = "no-store"
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/session/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_durable_session(
    *,
    response: Response,
    token_request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    """Mint access only from a still-active, exact signed PostgreSQL family."""
    refresh_token = token_request.refresh_token
    payload = security.decode_token(refresh_token)
    if not security.is_modern_refresh_token_payload(payload):
        raise HTTPException(status_code=401, detail="Refresh de sesión inválido.")
    try:
        allowed = await session_ledger.is_active(
            db, sid=payload["sid"], subject=payload["sub"],
            refresh_token=refresh_token, for_update=True,
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
    response.headers["Cache-Control"] = "no-store"
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
    if session_ledger.signed_refresh_family_for_replay(token) is None:
        # Old SID-less refresh still has a distinct rejection contract while
        # expired signed modern refresh may only ACK an earlier exact COMMIT.
        payload = security.decode_token(token)
        if security.is_refresh_token_payload(payload) and "sid" not in payload:
            raise HTTPException(
                status_code=409, detail="Token legado: requiere reautenticación.",
            )
        raise HTTPException(status_code=400, detail="Refresh de sesión inválido.")
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
    db: AsyncSession, refresh_token: str, *, for_update: bool = False,
) -> dict[str, str]:
    """Validate signed purpose, exact session digest and current persisted role."""
    payload = security.decode_token(refresh_token)
    if not security.is_modern_refresh_token_payload(payload):
        raise HTTPException(status_code=401, detail="Sesión de navegador inválida.")
    try:
        active = await session_ledger.is_active(
            db, sid=payload["sid"], subject=payload["sub"],
            refresh_token=refresh_token, for_update=for_update,
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
    # An exact signed refresh family remains the only replay proof after
    # lost ACK, even if its JWT has expired. Never let a subsequent login
    # overwrite it while the browser still sends that cookie. The browser
    # normally evicts the cookie at Max-Age; no revoked/expired cookie here
    # is treated as proof that PostgreSQL confirmed a logout.
    prior_cookie = request.cookies.get(browser_session.COOKIE_NAME)
    if (prior_cookie and
            session_ledger.signed_refresh_family_for_replay(prior_cookie) is not None):
        raise HTTPException(
            status_code=409,
            detail="Confirmá la revocación del logout anterior antes de iniciar otra sesión.",
        )
    pair = await create_durable_login(
        response=response, form_data=form_data, db=db,
    )
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
    browser_session.require_credential_read_origin(request)
    token = browser_session.cookie_refresh_token(request)
    body = await _browser_access(db, token)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Origin"
    return body


@router.get("/browser/logout-proof", status_code=status.HTTP_200_OK)
async def browser_logout_proof(
    *,
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Recover CSRF for exact cookie retry after a lost logout ACK.

    A proof is not access and is not an indication that PostgreSQL committed
    revocation. No new bearer JWT or refresh cookie is issued here.
    """
    browser_session.require_credential_read_origin(request)
    signed = browser_session.cookie_refresh_token(request)
    # A signed expired refresh is proof of the exact family for retry only,
    # never a bearer credential or permission to mint another access token.
    if session_ledger.signed_refresh_family_for_replay(signed) is None:
        raise HTTPException(status_code=401, detail="Cookie de sesión inválida.")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Origin"
    return {"csrf_token": browser_session.csrf_value(signed)}


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
    result = await _browser_access(db, token, for_update=True)
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
    if session_ledger.signed_refresh_family_for_replay(token) is None:
        raise HTTPException(status_code=401, detail="Sesión de navegador inválida.")
    try:
        outcome = await session_ledger.revoke(db, refresh_token=token)
    except Exception as exc:
        logger.exception("Browser logout PostgreSQL ACK not confirmed")
        raise HTTPException(status_code=503, detail="Logout no confirmado.") from exc
    if outcome not in {"COMMITTED", "ALREADY_COMMITTED"}:
        raise HTTPException(status_code=401, detail="Sesión revocada o inválida.")
    browser_session.clear_refresh_cookie(response)

"""Browser-only refresh cookie and per-credential CSRF guard.

Only explicitly configured first-party origins may initiate credentialed
state changes. Browser JS never reads or stores the signed refresh JWT.
"""
from __future__ import annotations

from hashlib import sha256
from hmac import compare_digest, new
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response

from app.core.config import settings
from app.core.token_keys import signed_jwt_seconds_remaining

COOKIE_NAME = "fitflow_browser_refresh"
COOKIE_PATH = f"{settings.API_V1_STR}/auth/browser"
CSRF_HEADER = "X-CSRF-Token"


def _secure() -> bool:
    """All non-local profiles are HTTPS-only; test/dev is synthetic."""
    return settings.ENV not in {"development", "test"}


def _origin(request: Request) -> None:
    """Reject absent or untrusted Origin on all cookie-mutating POST routes."""
    origin = request.headers.get("origin")
    allowed = {item.rstrip("/") for item in settings.BACKEND_CORS_ORIGINS}
    if (
        origin is None
        or origin not in allowed
        or urlsplit(origin).scheme not in {"http", "https"}
        or request.headers.get("sec-fetch-site") == "cross-site"
    ):
        raise HTTPException(status_code=403, detail="Origen de sesión no autorizado.")


def require_credential_read_origin(request: Request) -> None:
    """Protect GETs returning signed access JWT or CSRF material.

    Cross-origin fetches carry Origin; same-origin GET may omit it, so
    require Fetch Metadata explicitly identifying a same-origin script read.
    This browser boundary does not replace authentication by signed cookie.
    """
    if request.headers.get("origin") is not None:
        _origin(request)
        return
    if (
        request.headers.get("sec-fetch-site") != "same-origin"
        or request.headers.get("sec-fetch-mode") not in {"cors", "same-origin"}
    ):
        raise HTTPException(status_code=403, detail="Origen de lectura no autorizado.")


def csrf_value(refresh_token: str) -> str:
    """Signed, session-bound proof, never a bearer credential by itself."""
    return new(
        settings.SECRET_KEY.encode("utf-8"),
        ("fitflow-browser-csrf-v1\x00" + refresh_token).encode("utf-8"),
        sha256,
    ).hexdigest()


def verify_state_change(request: Request, refresh_token: str) -> None:
    _origin(request)
    supplied = request.headers.get(CSRF_HEADER)
    if (
        supplied is None
        or len(supplied) != 64
        or not compare_digest(supplied, csrf_value(refresh_token))
    ):
        raise HTTPException(status_code=403, detail="CSRF inválido o ausente.")


def require_login_origin(request: Request) -> None:
    """Login itself must not be cross-origin forged into a victim browser."""
    _origin(request)


def cookie_refresh_token(request: Request) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not isinstance(token, str) or not token:
        raise HTTPException(status_code=401, detail="Sesión de navegador ausente.")
    return token


def set_refresh_cookie(response: Response, token: str) -> None:
    ttl = signed_jwt_seconds_remaining(token)
    response.set_cookie(
        key=COOKIE_NAME, value=token, max_age=ttl,
        path=COOKIE_PATH, httponly=True,
        secure=_secure(), samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Origin"


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME, path=COOKIE_PATH,
        secure=_secure(), httponly=True, samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Origin"

"""
Endpoints de autenticación (login).

• POST /api/v1/login/token
  – Recibe credenciales vía OAuth2PasswordRequestForm (username = email).
  – Devuelve un JWT firmado conforme a la configuración del proyecto.

Requisitos:
• AsyncSession (SQLAlchemy 2.x + asyncpg)
• security.verify_password   – comprueba contraseña en texto plano vs hash
• security.create_access_token – genera el JWT
"""

from __future__ import annotations

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import settings
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.token import Token

router = APIRouter(prefix="/login", tags=["login"])

@router.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
) -> Token:
    """
    Autentica a un usuario y devuelve un token JWT de acceso.

    • `username` del formulario = email.
    • Verifica la contraseña hasheada.
    • Incluye el rol en el payload para posterior autorización.
    """
    # 1) Buscar usuario por email (asíncrono)
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user: User | None = result.scalar_one_or_none()

    # 2) Validar credenciales
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3) Crear JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")
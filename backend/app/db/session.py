
# app/db/session.py
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# --------------------------------------------------------------------------- #
# Engine asíncrono (postgresql+asyncpg)
# --------------------------------------------------------------------------- #
DATABASE_URL = settings.DATABASE_URL_ASYNC

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,           # pon True para ver las queries
    pool_pre_ping=True,
    future=True,
)

# --------------------------------------------------------------------------- #
# Session factory
# --------------------------------------------------------------------------- #
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

# --------------------------------------------------------------------------- #
# Dependency para FastAPI
# --------------------------------------------------------------------------- #
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para FastAPI que provee una AsyncSession.
    Se asegura de cerrar la sesión cuando termina la request.
    """
    async with AsyncSessionLocal() as session:
        yield session  # se cerrará automáticamente al salir del contexto
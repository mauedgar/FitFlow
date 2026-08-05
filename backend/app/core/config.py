"""Configuración central de FitFlow.

Incluye:
- Modo dev/prod/test
- Configuración de DB (sync + async)
- JWT (access + refresh)
- CORS
- Email
- Logs
- Paginación
- Uploads
- Redis (opcional)
- Rate limiting (opcional)
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL, make_url

# Ruta absoluta al archivo .env
ENV_PATH = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Clase principal de configuración de FitFlow.

    Carga valores desde el archivo .env y expone propiedades derivadas
    como la URL asíncrona de la base de datos.
    """

    # -----------------------------------------------------------------------
    # CONFIG GENERAL
    # -----------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    ENV: str = "development"
    DEBUG: bool = True

    # -----------------------------------------------------------------------
    # BASE DE DATOS
    # -----------------------------------------------------------------------
    DATABASE_URL: str

    @property
    def DATABASE_URL_ASYNC(self) -> str:  # noqa: N802
        """Convierte la URL sincrónica en una URL asyncpg."""
        url: URL = make_url(self.DATABASE_URL)
        url = url.set(drivername="postgresql+asyncpg")
        return str(url)

    # -----------------------------------------------------------------------
    # JWT / AUTENTICACIÓN
    # -----------------------------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_ROTATION: bool = True

    # -----------------------------------------------------------------------
    # API
    # -----------------------------------------------------------------------
    API_V1_STR: str = "/api/v1"

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # -----------------------------------------------------------------------
    # EMAIL
    # -----------------------------------------------------------------------
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None

    # -----------------------------------------------------------------------
    # LOGS
    # -----------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # -----------------------------------------------------------------------
    # PAGINACIÓN
    # -----------------------------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # -----------------------------------------------------------------------
    # UPLOADS
    # -----------------------------------------------------------------------
    MEDIA_DIR: str = "media"
    MAX_UPLOAD_SIZE_MB: int = 5

    # -----------------------------------------------------------------------
    # REDIS
    # -----------------------------------------------------------------------
    REDIS_URL: str | None = None

    # -----------------------------------------------------------------------
    # RATE LIMITING
    # -----------------------------------------------------------------------
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # -----------------------------------------------------------------------
    # TESTING
    # -----------------------------------------------------------------------
    TESTING: bool = False


# Instancia global de configuración
settings = Settings()  # type: ignore[reportCallIssue]

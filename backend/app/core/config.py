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
from typing import Self
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
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

    # An omitted profile is production-safe: explicit local mode is required.
    ENV: str = "production"
    DEBUG: bool = False

    # -----------------------------------------------------------------------
    # BASE DE DATOS
    # -----------------------------------------------------------------------
    DATABASE_URL: str

    @property
    def DATABASE_URL_ASYNC(self) -> str:  # noqa: N802
        """Convierte la URL sincrónica en una URL asyncpg."""
        url: URL = make_url(self.DATABASE_URL)
        url = url.set(drivername="postgresql+asyncpg")
        return url.render_as_string(hide_password=False)

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
    # REDIS
    # -----------------------------------------------------------------------
    REDIS_URL: str | None = None

    @staticmethod
    def _valid_serialized_origin(origin: str, schemes: set[str]) -> bool:
        """Require a browser Origin, not an arbitrary HTTPS URL.

        Origin serializes as scheme://host[:port] without path, query,
        fragment, credentials, whitespace, invalid port or trailing slash.
        """
        if not isinstance(origin, str) or not origin or any(
            ch.isspace() or ch == "\\\\" for ch in origin
        ):
            return False
        try:
            parsed = urlsplit(origin)
            port = parsed.port  # Raises ValueError for invalid/out-of-range ports.
        except ValueError:
            return False
        return (
            parsed.scheme in schemes
            and bool(parsed.hostname)
            and bool(parsed.netloc)
            and parsed.username is None
            and parsed.password is None
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
            and not parsed.netloc.endswith(":")
            and (port is None or port > 0)
            and origin == f"{parsed.scheme}://{parsed.netloc}"
        )

    @model_validator(mode="after")
    def validate_staging_contract(self) -> Self:
        """Reject HTTP credential origins and unsafe implicit environments."""
        if self.ENV not in {"development", "test", "staging", "production"}:
            raise ValueError("ENV must explicitly name a supported profile")
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if self.ENV in {"development", "test"}:
            if any(
                not self._valid_serialized_origin(origin, {"http", "https"})
                or urlsplit(origin).hostname not in local_hosts
                for origin in self.BACKEND_CORS_ORIGINS
            ):
                raise ValueError("Local profiles require loopback CORS origins")
            return self

        if self.DEBUG:
            raise ValueError("DEBUG must be false in staging or production")
        if self.ENV == "staging" and self.REDIS_URL is None:
            raise ValueError("REDIS_URL is required in staging")
        if not self.BACKEND_CORS_ORIGINS:
            raise ValueError("BACKEND_CORS_ORIGINS is required in staging or production")
        for origin in self.BACKEND_CORS_ORIGINS:
            if not self._valid_serialized_origin(origin, {"https"}):
                raise ValueError("HTTPS serialized CORS origins are required in staging or production")
            if urlsplit(origin).hostname in local_hosts:
                raise ValueError("localhost CORS origins are forbidden in staging or production")
        return self

    # -----------------------------------------------------------------------
    # VALIDADORES
    # -----------------------------------------------------------------------

    @field_validator(
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "EMAILS_FROM_EMAIL",
        "REDIS_URL",
        mode="before",
    )
    def empty_to_none(cls, v):  # noqa: ANN001, ANN201, N805
        """Convierte strings vacíos ("") en None.
        Esto evita errores cuando el .env contiene líneas como:
            SMTP_PORT=
        que de otra forma causarían fallos de validación.
        """  # noqa: D205
        if v == "":
            return None
        return v

    # -----------------------------------------------------------------------
    # LOGS
    # -----------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize supported Python log levels and reject silent mistakes."""
        normalized = value.upper()
        if normalized not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError("LOG_LEVEL must be CRITICAL, ERROR, WARNING, INFO, or DEBUG")
        return normalized

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

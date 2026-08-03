# backend/app/core/config.py

# Construimos una ruta absoluta al archivo .env. Esto es mucho más robusto.
# __file__ -> .../backend/app/core/config.py
# .parent -> .../backend/app/core
# .parent -> .../backend/app
# .parent -> .../backend
# .parent -> .../fitflow/ (la raíz del proyecto)
# Y finalmente le añadimos '.env'
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL, make_url  # ← esta línea

ENV_PATH = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    # BaseSettings ahora se configura con un `model_config`
    # Esto le dice a Pydantic dónde buscar el archivo .env
    # model_config = SettingsConfigDict(
    #     env_file=str(ENV_PATH),
    #     env_file_encoding='utf-8',
    #     case_sensitive=True,
    #     extra='ignore' # Ignora variables extra que no definamos aquí
    # )

    # Base de Datos: CRÍTICO. Si no lo encuentra en el .env, la app fallará (¡bien!)
    DATABASE_URL: str
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        url: URL = make_url(self.DATABASE_URL)
        url = url.set(drivername="postgresql+asyncpg")
        return str(url)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # JWT: Con valores por defecto por si no están en el .env
    SECRET_KEY: str = "un-secreto-muy-seguro-por-defecto-cambiame"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    API_V1_STR: str = "/api/v1"

# Creamos una única instancia que se usará en toda la aplicación
settings = Settings()
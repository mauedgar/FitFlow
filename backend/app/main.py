# backend/app/main.py
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core import readiness
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FitFlow API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Incluimos el enrutador de la v1 con un prefijo
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():  # noqa: ANN201, D103
    return {"message": "Welcome to FitFlow API"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    """Confirm that the application process can answer requests."""
    return {"status": "alive"}


@app.get("/health/ready", response_model=None)
async def readiness_status() -> JSONResponse:
    """Confirm that dependencies required by the beta vertical are usable."""
    unavailable = await readiness.get_unavailable_dependencies()
    if unavailable:
        logger.error("Readiness check failed for: %s", ", ".join(unavailable))
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(content={"status": "ready"})

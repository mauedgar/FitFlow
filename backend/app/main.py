# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="FitFlow API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)
# ⭐ 2. Define de dónde permites peticiones
# Para desarrollo, puedes permitir tu servidor de Vite.
# En producción, aquí iría la URL de tu dominio.
origins = [
    "http://localhost:5173", # La URL de tu app de React con Vite
    "http://localhost:3000", # Por si usas Create React App
]
# ⭐ 3. Añade el middleware a tu aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos los encabezados
)
# Incluimos el enrutador de la v1 con un prefijo
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():  # noqa: ANN201, D103
    return {"message": "Welcome to FitFlow API"}

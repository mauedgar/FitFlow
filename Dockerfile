# === ETAPA 1: COMPILACION ===
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# 1. Manifiestos primero: maximiza cache de capas
COPY pyproject.toml uv.lock ./

# 2. Instalar dependencias (projecto no-paquete: package=false en pyproject.toml)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 3. Copiar el codigo de la aplicacion backend
COPY backend ./backend

# === ETAPA 2: PRODUCCION (imagen ligera) ===
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x /app/backend/start.sh

EXPOSE 8000

CMD ["/app/backend/start.sh"]
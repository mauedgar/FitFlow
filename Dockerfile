# === ETAPA 1: COMPILACIÓN ===
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

# 1. Copiar y congelar dependencias globales de la raíz
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copiar solo el código de tu aplicación backend
COPY ./backend /app/backend
COPY ./pyproject.toml ./uv.lock /app/

# 3. Finalizar la instalación del proyecto (Generará un .venv limpio en /app/.venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


# === ETAPA 2: PRODUCCIÓN (Imagen Ligera) ===
FROM python:3.11-slim

WORKDIR /app

# 1. Traer el entorno virtual nativo de Linux (compilado en la etapa 1)
COPY --from=builder /app/.venv /app/.venv

# 2. Copiar tu código fuente
COPY ./backend /app/backend

# 3. Configurar las variables para que use este .venv de producción
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# 4. Ajustes finales e inicio
RUN chmod +x /app/backend/start.sh
EXPOSE 8000

CMD ["/app/backend/start.sh"]
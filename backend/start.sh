#!/bin/bash

# Aplicar las migraciones de la base de datos
echo "Applying database migrations..."
alembic upgrade head

# Iniciar el servidor FastAPI con Uvicorn
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
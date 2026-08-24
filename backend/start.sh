#!/bin/sh
set -e

cd "$(dirname "$0")"

echo "Applying database migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
if [ "${UVICORN_RELOAD:-0}" = "1" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

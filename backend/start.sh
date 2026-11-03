#!/bin/sh
set -e

cd "$(dirname "$0")"

echo "Verifying explicit proxy trust before database migrations..."
# Docker's actual frontend peer must be explicitly trusted; never trust '*'
# or arbitrary forwarded headers from the direct host-only backend port.
proxy_ip="${FITFLOW_TRUSTED_PROXY_IP:-}"
if [ "${ENV:-development}" = "staging" ] && [ -z "$proxy_ip" ]; then
    echo "FITFLOW_TRUSTED_PROXY_IP required in staging" >&2
    exit 1
fi
if [ -n "$proxy_ip" ]; then
    python - "$proxy_ip" <<'PY'
import ipaddress
import sys
try:
    ip = ipaddress.IPv4Address(sys.argv[1])
    if not ip.is_private or ip.is_loopback or ip.is_multicast or ip.is_unspecified:
        raise ValueError("unsafe trusted-proxy IPv4")
except ValueError:
    raise SystemExit("FITFLOW_TRUSTED_PROXY_IP must be a single private IPv4 address")
PY
    set -- --proxy-headers --forwarded-allow-ips "$proxy_ip"
else
    set -- --no-proxy-headers
fi
echo "Applying database migrations..."
alembic upgrade head
echo "Starting FastAPI server..."
if [ "${UVICORN_RELOAD:-0}" = "1" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload "$@"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"

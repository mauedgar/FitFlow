#!/usr/bin/env bash
# Only in disposable CI network; never use against fitflow-staging or retained volumes.
set -euo pipefail
: "${IR016_PROJECT:?Missing unique disposable project name}"
[[ "${IR016_PROJECT}" =~ ^fitflow-ir016-[0-9]+$ ]] || exit 2
[[ "${CI:-}" == "true" && "${FITFLOW_IR016_DISPOSABLE:-}" == "1" ]] || exit 2
compose=(docker compose --project-name "$IR016_PROJECT" --file docker-compose.staging.yml)
network="${IR016_PROJECT}_edge"
image="$("${compose[@]}" images -q backend)"
[[ -n "$image" ]] || { echo "IR016_BACKEND_IMAGE_MISSING"; exit 3; }

real_client() {
  local ip="$1" account="$2" count="$3" last="$4"
  docker run --rm --network "$network" --ip "$ip" --read-only \
    --cap-drop=ALL -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$PWD/scripts/ci/ir016_disposable_ingress_client.py:/tmp/ir016_client.py:ro" \
    --entrypoint python "$image" /tmp/ir016_client.py \
    --user "$account" --count "$count" --last "$last"
}
origin_key() {
  python - "$1" "$2" <<'PY'
import hashlib, hmac, os, sys
identity = (sys.argv[1] + ":" + sys.argv[2].strip().casefold()).encode()
print("auth_login_rate:hmac:" + hmac.new(os.environ["SECRET_KEY"].encode(), identity, hashlib.sha256).hexdigest())
PY
}
redis() { "${compose[@]}" exec -T redis redis-cli --raw "$@"; }
expect_origin_count() {
  local actual key
  key="$(origin_key "$1" "$2")"
  actual="$(redis GET "$key")"
  [[ "$actual" == "$3" ]] || { echo "IR016_SOURCE_ORIGIN_COUNT_FAILED"; exit 4; }
}
verify_header_spoof_is_ignored() {
  local key count
  for ip in 198.51.100.77 203.0.113.77 192.0.2.77; do
    key="$(origin_key "$ip" fitflow-ir016-a@example.invalid)"
    count="$(redis EXISTS "$key")"
    [[ "$count" == 0 ]] || { echo "IR016_UNTRUSTED_HEADER_SPOOF_FAILED"; exit 4; }
  done
}
real_client 172.30.251.20 fitflow-ir016-a@example.invalid 11 429
real_client 172.30.251.21 fitflow-ir016-a@example.invalid 1 401
real_client 172.30.251.20 fitflow-ir016-b@example.invalid 1 401
expect_origin_count 172.30.251.20 fitflow-ir016-a@example.invalid 11
expect_origin_count 172.30.251.21 fitflow-ir016-a@example.invalid 1
expect_origin_count 172.30.251.20 fitflow-ir016-b@example.invalid 1
verify_header_spoof_is_ignored
echo "IR016_TWO_SOURCE_NGINX_UVICORN_RATE_LIMIT_PASS"

# Host direct route remains local for existing release/smoke, not public bypass.
status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  --header 'X-FitFlow-Refresh-Ack: v1' \
  --header 'X-Forwarded-For: 198.51.100.77' \
  --data 'username=fitflow-ir016-a%40example.invalid&password=synthetic-invalid' \
  http://127.0.0.1:18000/api/v1/auth/token)"
[[ "$status" == 401 ]] || { echo "IR016_DIRECT_HOST_ROUTE_FAILED"; exit 4; }
verify_header_spoof_is_ignored
echo "IR016_DIRECT_BACKEND_SPOOF_RESISTANCE_PASS"

# Required-ACK staged policy prevents headerless registration before DB and Redis.
status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  --data 'username=fitflow-ir016-a%40example.invalid&password=synthetic-invalid' \
  http://127.0.0.1:18080/api/v1/auth/token)"
[[ "$status" == 426 ]] || { echo "IR016_STAGING_ACK_POLICY_FAILED"; exit 4; }

# Recovery uses only a known synthetic key in this uniquely named disposable Redis.
key="$(origin_key 172.30.251.20 fitflow-ir016-a@example.invalid)"
[[ "$(redis EXPIRE "$key" 1)" == 1 ]] || exit 4
sleep 2
[[ "$(redis EXISTS "$key")" == 0 ]] || exit 4
real_client 172.30.251.20 fitflow-ir016-a@example.invalid 1 401
echo "IR016_ORIGIN_TTL_RECOVERY_PASS"

# Inventory never reads/prints legacy bearer-key contents; synthetic Redis only.
redis SET "refresh_token:eyJ.ir016-synthetic-not-a-real-JWT" fixture-only >/dev/null
inventory="$("${compose[@]}" exec -T -w /app/backend \
  -e FITFLOW_ALLOW_LEGACY_READONLY_INVENTORY=1 backend \
  python -m app.core.legacy_redis_inventory --ack-read-only --max-pages 10)"
echo "$inventory" | grep -q '"raw_no_ttl": 1'
[[ "$inventory" != *"eyJ.ir016"* ]] || { echo "IR016_INVENTORY_KEY_LEAK"; exit 4; }
echo "IR016_LEGACY_REDIS_READONLY_INVENTORY_PASS"
echo "IR016_DISPOSABLE_INGRESS_PASS"

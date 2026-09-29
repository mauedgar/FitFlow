"""Exercise the FitFlow MVP vertical through staging HTTP interfaces."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CLIENT_EMAIL = "m4-wave-b-client@example.com"
FRONT_DESK_EMAIL = "m4-wave-b-front-desk@example.com"
SMOKE_PASSWORD = "FitFlow-Smoke-Only-2026!"
GYM_CLASS_ID = "00000000-0000-4000-8000-000000000401"
SESSION_ID = "00000000-0000-4000-8000-000000000403"


def request(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    token: str | None = None,
    content_type: str | None = None,
    expected: int = 200,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if content_type:
        headers["Content-Type"] = content_type
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            status = response.status
            raw = response.read()
    except HTTPError as exc:
        status = exc.code
        raw = exc.read()
    if status != expected:
        safe_url = url.split("?", 1)[0]
        raise AssertionError(
            f"{method} {safe_url} returned {status}, expected {expected}"
        )
    if not raw:
        return status, None
    content = raw.decode("utf-8")
    try:
        return status, json.loads(content)
    except json.JSONDecodeError:
        return status, content


def login(api_url: str, email: str) -> dict[str, str]:
    payload = urlencode({"username": email, "password": SMOKE_PASSWORD}).encode()
    _, tokens = request(
        "POST",
        f"{api_url}/auth/token",
        body=payload,
        content_type="application/x-www-form-urlencoded",
    )
    assert tokens["access_token"] and tokens["refresh_token"]
    return tokens


def run(frontend_url: str, backend_url: str) -> None:
    frontend_url = frontend_url.rstrip("/")
    backend_url = backend_url.rstrip("/")
    api_url = f"{frontend_url}/api/v1"

    _, live = request("GET", f"{backend_url}/health/live")
    assert live == {"status": "alive"}
    _, ready = request("GET", f"{backend_url}/health/ready")
    assert ready == {"status": "ready"}
    _, frontend = request("GET", frontend_url)
    assert '<div id="root"></div>' in frontend
    _, openapi = request("GET", f"{api_url}/openapi.json")
    assert openapi["info"]["title"] == "FitFlow API"
    print("PASS runtime and frontend-backend proxy")

    client_tokens = login(api_url, CLIENT_EMAIL)
    client_access = client_tokens["access_token"]
    client_refresh = client_tokens["refresh_token"]
    _, current_user = request("GET", f"{api_url}/auth/me", token=client_access)
    assert current_user["email"] == CLIENT_EMAIL
    _, refreshed = request(
        "POST",
        f"{api_url}/auth/refresh?{urlencode({'refresh_token': client_refresh})}",
    )
    assert refreshed["access_token"]
    print("PASS client authentication and Redis-backed refresh")

    _, classes = request("GET", f"{api_url}/gym-classes/public")
    assert any(item["id"] == GYM_CLASS_ID for item in classes)
    _, session = request("GET", f"{api_url}/class-sessions/{SESSION_ID}")
    assert session["id"] == SESSION_ID and session["status"] == "scheduled"
    _, initial_capacity = request("GET", f"{api_url}/class-sessions/{SESSION_ID}/availability")
    assert initial_capacity["used"] == 0 and initial_capacity["available"] == 5
    print("PASS class, agenda session, and initial capacity visibility")

    booking_payload = json.dumps(
        {"status": "confirmed", "class_session_id": SESSION_ID}
    ).encode()
    _, booking = request(
        "POST",
        f"{api_url}/bookings/",
        body=booking_payload,
        token=client_access,
        content_type="application/json",
        expected=201,
    )
    assert booking["status"] == "confirmed"
    booking_id = booking["id"]
    _, client_bookings = request("GET", f"{api_url}/bookings/me", token=client_access)
    assert any(item["id"] == booking_id for item in client_bookings)
    print("PASS client booking and persisted client state")

    front_desk_tokens = login(api_url, FRONT_DESK_EMAIL)
    front_desk_access = front_desk_tokens["access_token"]
    _, front_desk_bookings = request(
        "GET",
        f"{api_url}/front-desk/sessions/{SESSION_ID}/bookings",
        token=front_desk_access,
    )
    assert any(item["id"] == booking_id and item["status"] == "confirmed" for item in front_desk_bookings)
    _, occupied_capacity = request(
        "GET",
        f"{api_url}/front-desk/sessions/{SESSION_ID}/capacity",
        token=front_desk_access,
    )
    assert occupied_capacity["used"] == 1 and occupied_capacity["available"] == 4
    _, checked_in = request(
        "POST",
        f"{api_url}/front-desk/sessions/{SESSION_ID}/bookings/{booking_id}/check-in",
        token=front_desk_access,
    )
    assert checked_in["status"] == "attended"
    print("PASS front-desk observation, capacity, and check-in transition")

    refresh_query = urlencode({"refresh_token": client_refresh})
    request(
        "POST",
        f"{api_url}/auth/logout?{refresh_query}",
        token=client_access,
        expected=204,
    )
    request("POST", f"{api_url}/auth/refresh?{refresh_query}", expected=401)
    print("PASS Redis-backed logout invalidation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend-url", default="http://127.0.0.1:18080")
    parser.add_argument("--backend-url", default="http://127.0.0.1:18000")
    args = parser.parse_args()
    try:
        run(args.frontend_url, args.backend_url)
    except (AssertionError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS FitFlow staging MVP vertical smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

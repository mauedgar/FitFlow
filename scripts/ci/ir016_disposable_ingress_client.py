"""Real TCP client behind Nginx, with only synthetic invalid login identities."""
from __future__ import annotations
import argparse
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--user", required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--last", type=int, required=True)
    a = p.parse_args()
    if not a.user.endswith("@example.invalid") or not 1 <= a.count <= 12:
        p.error("synthetic invalid fixture only")
    codes: list[int] = []
    for _ in range(a.count):
        req = Request("http://frontend:8080/api/v1/auth/token",
            data=urlencode({"username": a.user, "password": "synthetic-invalid"}).encode(),
            method="POST", headers={
                "X-FitFlow-Refresh-Ack": "v1",
                "X-Forwarded-For": "198.51.100.77",
                "X-Real-IP": "203.0.113.77",
                "Forwarded": "for=192.0.2.77",
            })
        try:
            with urlopen(req, timeout=15) as response:
                status = response.status
                retry = response.headers.get("Retry-After")
        except HTTPError as e:
            status = e.code
            retry = e.headers.get("Retry-After")
            e.close()
        if status == 429 and not (retry and retry.isdecimal() and 1 <= int(retry) <= 60):
            raise AssertionError("429 must return bounded Retry-After")
        codes.append(status)
    assert codes[:-1] == [401] * (a.count - 1), codes
    assert codes[-1] == a.last, codes
    print(f"IR016_REAL_CLIENT_HTTP_PASS count={a.count} last={codes[-1]}")

if __name__ == "__main__":
    main()

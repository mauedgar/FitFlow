---
document_id: FF-IR005-AUTH-REDIS-FRONTEND-20261102-001
status: review_required
source: https://github.com/mauedgar/FitFlow/pull/56#issuecomment-6589333418
authority: user_authorized_next_recommended_action
product_acceptance: false
merge_authorized: false
---

# IR005 repair: browser session/logout, roles, Redis errors, login hardening

This DRAFT successor of PR56 addresses independent IR005's F07–F09 and
A06–A09 without modifying production services, secrets, database schema,
migration code or the authoritative `develop` branch.

## Session contract and frontend role routing (F07/F08/A06/A09)

- `POST /auth/token` already returns an access/refresh pair. The frontend
  now accepts the *entire pair*, stores both credentials in per-tab browser
  `sessionStorage`, and never saves refresh tokens into `localStorage`.
  Older access-only localStorage state is not reused.
- After login and during rehydration, the frontend calls `GET /auth/me`
  with the signed access Bearer and uses its ORM-derived id/email/role/active,
  comparing the signed UUID/role claim with the response. A decoded token is
  checked for signed use marker and expiry, but decode itself is **not**
  treated as cryptographic verification; `/auth/me` is the authoritative
  server check.
- Clicking logout issues `POST /auth/logout` with the stored refresh token
  and access Bearer before clearing browser credentials. Failure to confirm
  backend revocation still clears the local session but returns `false` to
  display a warning; **must not claim server-side logout success**.
- Session storage is per tab; closing a tab without logout does not revoke
  a server refresh token until signed expiry, and a captured refresh
  credential remains a bearer risk. This is not equivalent to a secure
  HttpOnly-cookie/session redesign, which requires a versioned Product
  decision. No access-token immediate revocation is claimed.
- Backend and frontend use `teacher`, not `trainer`. The canonical
  role-to-route mapping sends `admin` to `/admin`, `client/teacher`
  to `/home`, `front_desk` to `/front-desk`, and unknown roles to
  `/landing`. Login, root guard and protected routes use that mapping.
- CI executes real TypeScript/Vite build plus Node tests of the route
  function and explicit login/logout source wiring. These are not a deployed
  Playwright browser E2E; Issue37 deployed E2E remains NOT_RUN.

## Redis and authentication hardening (F09/A07/A08/A09)

- All commands in the refresh store and blacklist execute under a
  command-level RedisError → ExternalServiceError mapping. An outage after
  successful Redis ping returns HTTP 503, not accidental HTTP 500, across
  login, refresh and logout.
- New Redis keys store *only an HMAC-SHA256 digest* derived from the token
  under the configured server secret. Existing raw-token refresh and
  blacklist keys remain **readable** during migration; logout deletes both
  registration forms and blacklists via the new hashed key. New keys retain
  remaining signed JWT `exp` lifetime, existing old key cleanup is
  deliberately deferred; no FLUSHDB, scanning or mass key deletion.
- Missing accounts now execute a dummy bcrypt verify instead of returning
  before bcrypt; disabled accounts perform verification but still fail
  with uniform HTTP 401. Non-test profiles have a fail-closed
  Redis-backed atomic per-IP/email HMAC login attempt limiter,
  10 attempts / 60 seconds, HTTP 429 + Retry-After on overflow. Tests may
  use `TESTING=true` to bypass the normal throttle path but exercise
  the limiter explicitly with disposable Redis using a controlled
  settings override. Timing behavior is not claimed constant-time across
  every legacy hash algorithm and hardware configuration.
- HTTP PG15/Redis7 tests verify live legacy-token HMAC compatibility,
  role changes before refresh, signed-token expiry logout and Redis
  failures after ping. No production Redis or database operations.

## Boundaries and next gate

No changed API paths, roles on server, migrations, dependencies or secrets.
Review exact Git SHA/tree with Python 3.11/3.12/3.13, Ruff, Pyright, Node22
TypeScript, bcrypt, schema, independent WEB_INLINE IR006. Accept only on
0 findings and 0 advisories after actual independent review; no automatic
acceptance, integration, issue closure, or deployment.

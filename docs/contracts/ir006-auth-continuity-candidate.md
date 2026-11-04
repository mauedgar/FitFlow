---
document_id: FF-IR006-F10-F11-AND-ADVISORIES-20261102-001
status: review_required
source: https://github.com/mauedgar/FitFlow/pull/57#issuecomment-6590256400
authority: user_authorized_next_dependency
product_acceptance: false
merge_authorized: false
---

# IR006 successor: bounded Redis login errors and active-session renewal

## Authority and change scope

Independent IR006 found F10/F11 and A10–A14 on PR57 frozen at
`6db7d9502f3ffda460a5dec9a2e9ecbb53b744c7`, tree
`428508a1771f89c6861ca84d03b4561e16eb175b`.
This candidate is a **successor**, not integration or acceptance. No
migrations, dependency changes, real Redis/DB operations or deployments.

## F10 · Redis errors before login lookup

`POST /auth/token` maps Redis failure of its login limiter to bounded
HTTP **503**, not an uncaught 500; both absent Redis configuration and
EVAL failures **after ping** are covered by negative HTTP tests in the
isolated PG15/Redis7 test profile with a scoped TESTING override.
No account lookup occurs when the limiter rejects the request.

## F11 · Active frontend session renewal

- A shared `ensureFreshAccess` single-flight routine updates access from
  `/auth/refresh` with the existing nonrotating refresh credential, only
  when near expiry or after an authorized request gets an HTTP 401.
- Request/response Axios interceptors handle protected API traffic. Login,
  registration, refresh and logout do not recurse; one retry only for
  protected HTTP 401. Explicit new-login `/auth/me` Bearer is not
  overwritten by stale session state. Refresh state is never restored
  after the underlying session refresh token changes or is removed.
- An access-expiry timer renews while the SPA remains mounted. AuthProvider
  listens for verified renewal/invalidity events, updates navigation role
  from the refreshed server-derived role and invalidates UI state on
  terminal auth errors. A network failure does not falsely claim
  server-side revocation or delete a still-registered refresh token.
- Rehydration against `/auth/me` remains authoritative. Transient network
  failure preserves unverified credentials (no authenticated UI), allowing
  recovery via `online`/reload. Failed post-login `/auth/me` attempts
  revocation before local clear; during network failure the paired
  credentials are retained, but not accepted until server verification.
- No immediate access revocation or cross-tab global logout is claimed.
  Refresh credentials remain in per-tab `sessionStorage`, not a
  server-issued HttpOnly cookie; XSS remains a security boundary.

## A12 · Rate-limit improvement and tradeoffs

Both per-IP+account and per-account HMAC keys are atomically incremented
under Redis Lua. The first allows 10 requests per 60 seconds; the second
caps distributed attempts at 30 per 60 seconds. HTTP 429 uses
`Retry-After` based on observed Redis remaining TTL. The account cap
also allows intentional lockout by an attacker and successes count toward
limits: those usability tradeoffs are **not** claimed eliminated, and
measured abuse-policy tuning is a separate Product decision. Synthetic
tests exercise distributed sources and non-test HTTP Redis failures;
no production keyspace or credential operations.

## A13 · Legacy raw-token Redis calls

New signed refresh tokens carry `jti`, and use hashed Redis keys only.
Fallback `EXISTS`/deletion for raw JWT keys is now limited to **pre-jti**
issued credentials to preserve their prior registration and revocation
semantics. Old raw keys are not bulk-migrated/deleted; a time-bounded
legacy key retirement after expiry is a separate production operation.
Legacy Redis command monitoring may still contain token text until then.

## A14 · Teacher landing

Teacher users now receive a dedicated panel with a clearly named
educational role and links to class browsing rather than a client agenda.
Assigned-class/attendance workflows are **not** invented: those remain
a separate Product feature. No backend teacher permissions were expanded.

## A10/A11 and remaining evidence limits

A10: post-login failures attempt server revocation when feasible; transient
network failures preserve unverified session for recovery, and explicit
logout still reports unconfirmed server revocation rather than fabricating
success. A11: TypeScript transpile+VM simulated API tests validate
concurrent renewal, 401 retry, exclusion of refresh endpoint and
login's explicit principal Bearer. These are more than static source
assertions but **are not browser-mounted or deployed E2E**; Issue37
deployed E2E remains NOT_RUN. An actual browser E2E is still required
to close that distinct evidence debt.

Full CI must qualify new immutable SHA/tree on PG15+Redis7 Python
3.11/3.12/3.13, Ruff, Pyright, Node22 TypeScript and tests, bcrypt,
schema and structure. Independent WEB_INLINE IR007 must reexamine the
integrated tree before recommending acceptance; 0 findings and
0 advisories is mandatory. Never merge/accept/close automatically.

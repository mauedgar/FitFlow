---
document_id: FF-IR007-REMEDIATION-20261102-001
status: review_required
authority: FITFLOW_CONTROL / user authorized repair of findings and advisories
source: https://github.com/mauedgar/FitFlow/pull/58#issuecomment-6590750122
acceptance: false
merge_authorized: false
---

# IR007 successor — protected catalog, teacher ownership, SPA races and privacy

## Frozen predecessor
IR007 reviewed PR58 commit `d161ce3ca4111e14d1ff523fee19d09e7f7bcea1`
tree `4cf976dfcda9597458900887e80cb0e837be433a` and returned
NO_RECOMMEND, 4 findings (1 HIGH/3 MEDIUM) and 6 advisories.
This successor is not accepted, integrated, deployed or closed.

## F12 — anonymous class mutations
POST/PUT/DELETE `/gym-classes` now require the active ORM-backed
`require_admin` principal. The public class catalogue endpoints remain
public/read-only. Isolated PostgreSQL HTTP tests reject anonymous requests
(401) and client/teacher/front-desk writers (403) without modifying classes;
admin role retains the competent API path.

## F13/F14 — session generation
The Axios client attaches a private generation marker only to requests for
which it authoritatively supplied a Bearer. A late 401 from an old access
token in **the same refresh session** reuses the already-renewed current
access credential instead of issuing a redundant refresh. An older login
or logout session generation cannot retry against a new user, and explicit
new-login tokens are not intercepted as session-owned.
AuthProvider uses a monotonic session epoch for rehydration, login, logout
and reset; a pending response is discarded when epoch/refresh identity has
changed. Re-verification clears old UI state first. Expiring access renewal
and failure signals are retained. Independent review must assess async
races beyond isolated VM tests.

## F15 — teacher account/profile identity
The private teacher GET/PUT authorization resolves Teacher (joined to
Person) by profile UUID and verifies `Person.user_id` against signed,
active ORM-derived account identity, not `Teacher.id` equality.
Admins retain normal access. Non-owner or nonexistent profiles fail
permission check with 403 without revealing profile data. Isolated PG15
tests exercise real teacher account/profile UUID inequality and HTTP
positive owner/admin and negative unrelated roles.

## Advisories
- **A10 network orphan:** original login response can be lost *after*
  registration in Redis; no client that never received the pair can
  revoke it. Signed TTL bounds registration; existing best-effort
  revocation on post-login verification and local unverified recovery
  remain. No claim of deterministic server-side compensation.
- **A11 browser E2E:** added VM-executed staggered concurrent 401 and
  old-session rejection tests and static source guard; **not** deployed
  browser E2E or React mounted click testing. Issue37 remains NOT_RUN.
- **A12 limiter:** staging configuration now refuses `TESTING=true`,
  which previously bypassed the limiter. Reverse proxy/shared-client
  identity and account-wide lockout tradeoffs still require deployment
  policy and direct staged verification. No trust in arbitrary forwarded
  IP headers is added.
- **A13 Redis legacy:** raw JWT fallback is still required for signed
  pre-jti legacy refresh tokens. New keys use HMAC/TTL; no unsafe key
  migration or mass deletion. Raw-token command monitoring for legacy
  calls remains until the compatibility window and a separately
  authorized retirement.
- **A15 admin teacher screen:** removed fictional client identities
  and nonfunctional mutation actions. The view transparently reports
  unavailable teacher management. A real admin teacher UI/list will
  require a separate scoped Product implementation.
- **A16 bookings privacy:** booking-level UUID, status and timestamps
  are no longer anonymously enumerable on session/class/schedule/day/
  range routes, despite their historical `/public` names. Access is
  limited to ORM-backed operational roles (admin/teacher/front_desk).
  Client self-bookings remain via existing personal contract; public
  aggregate capacity API is unaffected. Real HTTP negative checks
  cover 401/403. This is an intentional restriction of the old
  public read behavior and requires independent compatibility review.

Tests and CI must associate exact successor SHA/tree with backend
Python 3.11/3.12/3.13, PG15/Redis7, Ruff, Pyright, frontend TypeScript,
Node simulation, bcrypt, schema and structure. No production DB,
real credentials, schema migration, dependency or deployment changes.
A fresh independent WEB_INLINE IR008 review must return 0 findings and
0 advisories before **recommending** acceptance; no auto-accept/merge/close.

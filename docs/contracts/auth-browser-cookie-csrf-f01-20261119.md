---
document_id: FF-ISSUE108-F01-BROWSER-COOKIE-20261119-001
status: candidate_not_accepted
issue: 108
baseline: develop@276481de41f6829e8dd7beed79127e13237b5dcb
integration: false
---

# Browser authentication and CSRF: current PR118 candidate

This document supersedes earlier phase-specific statements that said the
frontend had not adopted cookies or /auth/token still issued new SID-less
credentials. PR118 is an UNMERGED SOURCE CANDIDATE, not deployed or accepted.

The SPA calls POST /auth/browser/token. Refresh lives in a host-only HttpOnly
SameSite=Lax cookie scoped to /api/v1/auth/browser, Secure outside explicit
test/development. JS receives access and a cookie-specific HMAC CSRF token,
never the refresh bearer. Access JWT remains in React memory and is
rehydrated by GET /auth/browser/session after PostgreSQL SID verification.
The browser no longer accepts, decodes or restores historical SID-less
access saved in localStorage: it discards that key unconditionally. The
frontend login contract requires both a modern access bearer and cookie-bound
CSRF; only in-memory access is accepted. API legacy credential handling
remains an independent backend cutover gate, not silently claimed complete.

Mutation POSTs /auth/browser/refresh and /auth/browser/logout require exact
allowlisted first-party Origin plus X-CSRF-Token; login requires Origin.
Credential-bearing GET /auth/browser/session and GET /auth/browser/logout-proof
require allowed Origin for cross-origin requests; for same-origin script GETs
without Origin, Fetch Metadata must confirm same-origin non-navigation.
Untrusted/absent origins without acceptable Fetch Metadata fail closed.
GET /auth/browser/logout-proof recovers ONLY the same-cookie HMAC proof for
idempotent retry after a lost logout ACK. It does not mint bearer or attest
revocation, and uses no-store. Logout returns HTTP204 and clears the cookie
ONLY after PG commit or verified exact replay; unconfirmed result is 503.
A browser login with an existing signed refresh cookie is rejected with 409
until logout clears it, even if PG already committed revocation but its ACK
was lost. This prevents overwriting an unreconciled session family's proof.

Cross-tab browser login/refresh/logout operations use one Web Lock; an
unsupported browser fails closed rather than silently racing the shared
cookie. Storage events send no JWT, refresh, CSRF or secrets; other tabs
invalidate stale access and rehydrate only from the authoritative cookie.
Unconfirmed logout blocks login and offers retry. Every retry retrieves the
current cookie proof and posts logout in the same cross-tab Web Lock, never
reusing a stale CSRF from another tab. If GET logout-proof returns 401 because
the signed cookie is unavailable or expired, the UI records
expired-unconfirmed, clears pending and CSRF markers across tabs and permits
a new credentialed login. This does NOT assert a PostgreSQL COMMIT or claim
that an earlier access token was revoked: such a token remains valid only
until its original signed expiration if its old ledger family is active.
POST failure/uncertain revocation remains pending rather than inventing
a 204. Transient refresh failures retain bounded retry/generation guards.
These guarantees require actual final-head browser and disposable HTTP
negative tests, and independent review; initial IR001 found 2 frontend
findings/2 advisories on the historical fd376... HEAD.

Legacy /auth/token new issuance is durable SID-backed, but the backend still
accepts existing signed SID-less refresh and may produce SID-less access bounded by its
original signed refresh expiry. Legacy access is NOT individually family
revocable; no immediate full legacy remote logout is claimed. After original
expiry, reauthentication is required. No unbounded extension or automatic
mass session invalidation.

Deployment STOP: retained PG migration NOT_RUN, no staging/prod activation,
no assumed cross-site SameSite=None fallback, CORS/HTTPS topology not
qualified, no secret rotation, no 0F0A final independent acceptance yet.

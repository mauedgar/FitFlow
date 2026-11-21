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

Current /auth/token new issuance is durable SID-backed. The current HTTP
refresh endpoints reject signed SID-less refresh even if Redis retains an
old registration; no SID-less access can be minted or refreshed by them.
The strict modern bearer gate also rejects historically issued SID-less
and untyped access tokens even before their signed expiry. These artifacts
cannot be retroactively assigned a family; reauthentication is required.
Historically issued tokens might remain cryptographically signed until exp,
but that is not a claim of present endpoint acceptance or family revocation.

Deployment STOP: retained PG migration NOT_RUN, no staging/prod activation,
no assumed cross-site SameSite=None fallback, CORS/HTTPS topology not
qualified, no secret rotation, no 0F0A final independent acceptance yet.

## Control 015 — Backend refresh cutover (candidate)

The /auth/refresh compatibility URL now authorizes only signed, typed,
PG-registered refresh tokens with sid; legacy untyped and typed SID-less
refresh never issue new access, even if a historical Redis entry exists.
The original /auth/logout alias and signed SID-less bearer gates have also
cut over to PostgreSQL SID-only authority. No token lifetime extension.

## Control 015 — historical logout alias cutover (candidate, not merged)

POST /auth/logout now rejects SID-less refresh even if Redis registration
existed. It requires a signed modern refresh family and the current access
subject owner, then revokes the exact PostgreSQL row. After committed
revocation, a lost ACK can be reconciled by /auth/session/logout without an
access bearer. Strict signed SID-bearing access guards are already implemented in this
candidate; signed SID-less bearer is rejected, not an open compatibility path.

## Control 015 — strict modern bearer gate (candidate, not accepted)

Both `get_current_user` and `get_user_from_token` require signed,
typed access JWTs containing a canonical UUID subject, canonical UUID4 SID
and declared role; every request checks the SID against the live
PostgreSQL family before loading user. Signed old SID-less or untyped tokens
and email-subject tokens are invalid even before expiry. The old browser
localStorage compatibility path was already retired. Ten real HTTP test
domains now register synthetic PG sessions with signed refresh digest using
a disposable test-only helper (no Product TESTING bypass). All user/domain
claims and signing still flow through standard Product paths.
Native CI and complete independent review on frozen candidate are required.

## Control 015 — IR003 source repairs (candidate, not accepted)

- A delayed successful login response is bound to the auth generation at
  dispatch; if another tab reports a later logout, its HTTP 200 cannot
  re-establish React identity or navigate to a protected page.
- Browser refresh takes the exclusive cookie Web Lock *before* acquiring
  the current cookie-bound CSRF proof. It no longer sends a proof captured
  before waiting for another tab's cookie transition.
- AdminSessionGate uses only the current in-memory bearer for 401 matching,
  never a historical localStorage credential.
- The browser regression suite adds a held successful login delivery and
  a queued refresh after a concurrent signed cookie replacement.
- A refresh JWT may be signature-verified beyond expiry solely as a key to
  verify exact *already committed* PostgreSQL logout replay, with owner,
  SID and constant-time refresh digest match. Expired credentials still
  cannot revoke active families, mint access or authenticate.

## Control 015 — IR004 security profile and fixture repairs (candidate)

Missing ENV defaults to fail-closed production (DEBUG false). Any unknown
profile denies startup. Staging and production require explicit HTTPS
credential origins with nonlocal hostnames; staging still requires Redis.
Explicit development/test profiles can use non-Secure cookies only with
loopback CORS origins. The cancellation and P0 security suites now invoke
the same localhost + fitflow_test + ENV=test + TESTING guard before any
synthetic INSERT, including no-auth tests. CI and new independent review
must revalidate this candidate before Product acceptance.

## Control 015 — IR004 bounded browser Web Lock (candidate)

The exclusive cookie mutation Web Lock has a total 12-second budget
including queue acquisition and network work. Each login, refresh and
signed logout operation propagates the AbortSignal into its Axios
requests. A stalled proof GET cannot retain the mutation lock without
a bounded cancellation; an aborted logout remains unconfirmed in UI.
Legacy logoutBrowserSession accepts its old argument but ignores that
stale proof and delegates to the exact cookie proof read under the lock.
A signed two-tab Playwright regression intentionally stalls the proof
GET and checks that another tab regains login responsiveness. Review and
exact-head CI are required; this is not a guarantee against a backend
commit whose HTTP ACK was lost.

## IR006 S04 candidate repair — local and shared epoch barriers

An accepted same-tab logout increments the auth generation synchronously
before clearing memory and initiating durable cookie logout. An in-flight
refresh cannot repopulate Axios bearer or React auth state after logout,
even if its HTTP 200 arrives before the exact PostgreSQL revoke ACK.
A repeated same-tab logout joins the original retry and does not bump the
generation again.

All asynchronous browser restore and refresh responses now compare the
current shared localStorage auth epoch at acceptance time rather than rely
only on delivery of storage events. LoginPage also rejects a late login
response after that shared epoch changes. This does not claim that
localStorage is a security token; it is a nonsecret invalidation marker.
A real Playwright signed refresh response is held across a same-tab logout
to exercise these boundaries. CI/independent review on the new SHA required.



## IR006 S02 — Signed expired-cookie boundary and final user lookup

The browser login gate rejects any still-present *signed* modern refresh
family cookie, even when its JWT has passed its signed expiry. Such a cookie
is still useful as an identity for an exact lost-ACK reconciliation, but
it is never proof of a PostgreSQL revocation. The server returns HTTP409
without Set-Cookie or new PG session issuance. Normal browsers remove
expired cookies according to Max-Age; a test forces an anomalously retained
cookie and proves that a subsequent login requires it to be discarded
first. No product path calls this a confirmed logout. Invalidly signed
cookies are not considered replay proof.

The bearer guard also maps a PostgreSQL failure during its final user
lookup to the same HTTP503 persistence-unavailable contract as an error
during the SID ledger lookup. Both cases have dedicated negative HTTP tests.

## FitFlow C015 — IR008 monotonic cross-tab logout receipt (candidate)

- A `logout-pending` signal carries a random nonsecret operation UUID.
  A surviving or reloaded tab retains the same operation identity locally
  while attempting to revoke the shared signed HttpOnly cookie.
- A real HTTP 204 from PostgreSQL is the only source of a
  `fitflow_logout_confirmed_operation` marker. It is recorded inside
  the exclusive browser cookie Web Lock before releasing it, so a queued
  peer receiving proof GET 401 cannot downgrade the same confirmed logout.
- Missing or expired cookie without a matching 204 marker is still
  `expired-unconfirmed`, never a manufactured server ACK. Other operation
  IDs cannot settle the pending operation or erase newer login state.
- Browser E2E holds the origin 204 while a surviving peer queues on
  the Web Lock and checks the old signed bearer is really revoked.
  The separate single-tab test preserves missing-cookie/no-ACK behavior.
- Authenticated missing, deleted and inactive user principals uniformly
  return HTTP 401 with Bearer challenge, while registered SID ledger
  or final user database outages remain HTTP 503 without exception leaks.
- These are candidate semantics pending exact-HEAD CI and a new
  independent review; this document does not accept the Product.

## Current PR118 candidate behavior (supersedes older stage notes)

| HTTP route | Accepted credential | Security authority | Returned credential |
|---|---|---|---|
| POST /auth/token, /auth/session/token | Password plus live User | PostgreSQL AuthSession COMMIT | Typed SID access + refresh |
| POST /auth/refresh, /auth/session/refresh | Signed typed SID refresh | PostgreSQL registered active SID + exact digest | Typed SID access only |
| POST /auth/logout | Signed typed SID refresh + owner access | PostgreSQL exact family COMMIT | 204 after COMMIT/replay |
| POST /auth/session/logout | Signed typed SID refresh | PostgreSQL exact family COMMIT/replay | 204 after confirmed result |
| POST /auth/browser/token | Password and allowed Origin | PostgreSQL + HttpOnly signed cookie | In-memory access + CSRF, no refresh JSON |
| GET /auth/browser/session | Signed cookie and allowed Origin | PostgreSQL live family | In-memory access + CSRF |
| POST /auth/browser/refresh | Cookie plus Origin and CSRF | PostgreSQL live family under row lock | In-memory access + CSRF |
| POST /auth/browser/logout | Cookie plus Origin and CSRF | PostgreSQL COMMIT/replay | Cookie cleared only after actual 204 |

The current bearer guards reject historical signed SID-less or untyped
access tokens. Old Redis registration keys are not an HTTP refresh
fallback. All these statements describe **candidate code**, not an accepted
merge, deployed behavior or proof independent of actual tests.

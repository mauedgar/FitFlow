---
document_id: FF-ISSUE108-F01-BROWSER-COOKIE-20261119-001
status: combined_source_candidate_unaccepted
baseline: PR118@fd376994da9698350fe7f86058be5ca6add66e92
issue: 108
integration: false
---

# First-party modern browser sessions — CSRF and cookie candidate

This first F01 successor is isolated from the existing PR117 branch.
New browser routes are /auth/browser/token (FORM),
/auth/browser/session (read-only bootstrap), /auth/browser/refresh (POST),
and /auth/browser/logout (POST). The JSON never returns a refresh JWT.
Browser refresh is in a host-only HttpOnly cookie scoped to the browser-auth
path, SameSite=Lax, with Secure in all non-local profiles; development/test
HTTP exception is explicit and NEVER authorized as a production setting.
No session secrets go into localStorage by these new endpoints.

Cookie POST requires **exact configured first-party Origin**,
rejects Sec-Fetch-Site cross-site, and compares a per-credential HMAC
derived via server secret and presented in X-CSRF-Token (login requires
Origin before any cookie exists). Browser JS obtains CSRF from the login
response or read-only authenticated bootstrap and only uses it in a
custom header. Cross-origin consumers not sharing the same site will
not receive Lax cookies; production requires a same-site frontend/API or
an approved reverse proxy, not automatic SameSite=None.

PostgreSQL remains the only durable revocation authority for SID-bearing
modern cookies. Browser logout returns 204 and clears cookie only after
a durable transaction or an exact committed replay; uncertainty returns
503 and preserves cookie for retry. Both guards check the PostgreSQL SID.

**Historical stage 1 (superseded at current PR118 HEAD):** the initial backend-only
increment had not integrated frontend and the old default issuer still
minted SID-less tokens. Current PR118 frontend now uses the browser cookie
session endpoints and /auth/token now issues PostgreSQL-backed SID families.
This is an implemented *candidate*, not Product acceptance or deployment. No retained migration,
production cookie activation, credentials, staging or deploy.


## SPA/browser integration successor (not integrated)

New login invokes /auth/browser/token with credentials and receives
access+CSRF, never a raw refresh JWT. Refresh cookie is scoped to
/auth/browser and inaccessible via JavaScript. Modern access is held
only in React memory and rehydrated after reload via GET
/auth/browser/session, which checks the durable PostgreSQL SID.

The UI uses X-CSRF-Token for cookie refresh/logout, withCredentials,
and an explicit PENDING state whenever server-side logout ACK is
not confirmed; retry is offered and 204 is the sole success signal.
Existing signed SID-less access already in localStorage may still be
read until its original exp, but the new browser flow does not
create localStorage entries for modern credentials.

**Historical stage 2 (superseded):** these earlier default-issuer and E2E
assumptions were repaired in later PR118 commits. Current source CI is green,
but the full 39-path independent security review, unresolved legacy access
window and production migration remain separate gates.



## F01 issuer cutover candidate, subject to exact-SHA CI and IR

The old /auth/token endpoint keeps its original TokenPair response shape but
**no longer issues new SID-less JWTs**. Every successful API login now creates
a signed UUID4 family in PostgreSQL and returns only after committed durable
registration; an uncertain COMMIT yields 503 with no credentials. No Redis
registration is needed for modern sessions, even when Redis is unavailable.

The historical /auth/refresh and /auth/logout endpoints route SID-bearing
signed refresh tokens to the same PostgreSQL session authority. Their SID-less
legacy paths remain read-only-compatibility through original JWT expiration
and continue using their old Redis blacklist/registration semantics. The
browser flow uses only HttpOnly cookies and memory-held access JWTs. No
blanket user/session invalidation, retained Redis cleanup or token rewriting
is authorized. New credential issuance is scoped to the original secure
authentication routes, not test factories that explicitly manufacture
legacy signed tokens to verify compatibility.

Current PR118 source is unaccepted: implemented frontend cookie, logout ACK,
and negative HTTP tests must still be independently reviewed
on frozen SHA/tree before Product acceptance and nonforced merge. Staging,
retained-data migration and production remain NOT_RUN.


## Effective status at current PR118 candidate

Head `fd376994da9698350fe7f86058be5ca6add66e92` is IMPLEMENTED_SOURCE_CANDIDATE,
NOT_ACCEPTED, NOT_MERGED, NOT_DEPLOYED. Legacy SID-less access JWTs may remain
valid only until signed expiry. Legacy refresh may issue a bounded SID-less
access (not beyond the original signed refresh expiry), outside modern durable
family revocation. This finite compatibility tradeoff and the lack of a
retained migration, production origin qualification or final 0F/0A IR
must not be misrepresented as globally durable logout.

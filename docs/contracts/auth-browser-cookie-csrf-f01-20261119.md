---
document_id: FF-ISSUE108-F01-BROWSER-COOKIE-20261119-001
status: backend_candidate_unaccepted
baseline: PR117@c4ce5f882f8d3c605cbb278b0099e2fd5a2f162d
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

**THIS FIRST INCREMENT DOES NOT YET ADOPT THESE ROUTES FROM THE FRONTEND**
and does not stop /auth/token legacy SID-less issuance, so F01 remains
OPEN/HIGH and PR117/this successor are NOT approved for integration.
A further coordinated frontend/default-token cutover with native full
CI, browser network-recovery tests, legacy expiration policy and
independent full security IR is mandatory. No retained migration,
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

STILL OPEN: legacy /auth/token default issuance and old browser E2E
assumptions; do not claim F01 closed until those are migrated,
all new-SHA tests/browser E2E pass, and full security IR approves.

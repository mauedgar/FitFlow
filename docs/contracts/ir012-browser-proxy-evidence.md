---
document_id: FF-IR012-BROWSER-PROXY-20261103-001
status: independent_review_required
authority: user_approved_next_priority_A11_A12_and_conditional_0F0A_PR_integration
predecessor: https://github.com/mauedgar/FitFlow/pull/62#issuecomment-6594063857
product_acceptance: false
merge_authorized_unconditionally: false
---

# A11 + A12 — bounded browser and proxy evidence

## Source of truth and predecessor

FitFlow PR62 candidate `7b74f92ca4adc462d60bc3a19956587f62c60f51`,
tree `dd7e470b5d04615d73d9e49194035c52252a778d`, was
qualified by independent WEB_INLINE IR011: **0 findings, 5 advisories,
NO_RECOMMEND**. Approved A16 teacher-assignment-scoped reads and A17
public/operational separation remain frozen. The user authorized the
next A11+A12 priority and separate acceptance/integration of PRs
with exact independent 0 findings and 0 advisories; this conditional
grant does not accept PR62, this candidate or any historical review.

## A11 — actual mounted Chrome, not a hypothetical Node DOM

New GitHub Actions workflow `.github/workflows/fitflow-mounted-browser-e2e.yml`
uses a disposable `ubuntu-24.04` runner with **preinstalled Chrome
and ChromeDriver**, existing Node22 and locked `npm ci --ignore-scripts`.
No Playwright dependency or browser download is introduced. The
runner checks out the PR head SHA and prints the exact Git tree.
`frontend/tests/browser/fitflow-mounted-e2e.cjs` starts Vite preview
for the real built React application, a synthetic HTTP API on
127.0.0.1:4180 and WebDriver-controlled real headless Chrome.

Bounded browser checks:
1. Anonymous catalogue renders a synthetic activity from the safe
   `/gym-classes/public` API, not the operational `/gym-classes/` API.
2. Unauthenticated navigation to `/admin` redirects to login.
3. Real email/password form input events, synthetic token-pair issuance,
   `/auth/me` verification and admin role navigation work.
4. A nearly-expired access token in sessionStorage triggers
   `/auth/refresh` during full reload and returns to the admin page.
5. Chakra profile-menu logout posts `/auth/logout`, clears the
   refresh credential and prevents reentry into `/admin`.

The test prints a deterministic `E2E_BROWSER_RECEIPT` including actual
Chrome version, request counts, a screenshot SHA256 and no real secrets.
All fixture values are synthetic, the test profile is removed on exit,
and the mock server/Vite/browser are stopped by the test. No real DB,
Redis, staging host, email provider or authentication secret is used.

**Limits:** This is a mounted browser **frontend integration test with
a mock API**, not a real staging deployment, not an end-to-end network
test against FastAPI+PostgreSQL+Redis, and does not cryptographically
verify the synthetic mock JWT. The existing real HTTP PG15/Redis7
tests qualify the backend separately. No deployment PASS is claimed.
A11 may be fully disposed only for the authorized browser-mode scope;
deployed auth/smoke remains in the staging gate if still required.

## A12 — proxy boundary evidence without changing deployed topology

The current login router uses `request.client.host` from the ASGI
scope and never directly treats arbitrary X-Forwarded-For, X-Real-IP or
Forwarded header strings as authenticated client identity.
The new synthetic HTTP regression test
`backend/tests/api/test_ir012_proxy_origin_http.py` submits all three
spoofed headers to the real mounted FastAPI app with an instrumented
throttle hook. It verifies that the ASGI peer origin, rather than
spoofed headers, is passed to the limiter. It also tests that staging
with `TESTING=true` fails during settings validation.

Existing Redis Lua limit tests separately establish atomic
10/60s per account+IP and 30/60s account-wide caps. These hermetic
tests do NOT establish which upstream address a live Uvicorn process
will receive behind an actual proxy, which proxy peers are trusted,
how shared-IP clients are treated or how account lockout is recovered.
No setting for trusting arbitrary forwarded headers is added.
Those properties require a competent staging/ingress configuration,
exact host identity and a separately bounded operational execution
grant before A12 can be marked fully resolved.

## Other advisories and acceptance boundary

A10 lost refresh response/orphan remains constrained by signed TTL,
without client revocation proof of undelivered credentials. A13 legacy
pre-jti raw-token Redis compatibility remains active and cannot be
removed without supported expiry evidence and separate production
migration authority. A18 additional schema-archive unpack and legacy
reverse Passlib matrix qualification remain separate; browser proof
is reported here only for the actual mounted browser scope.

Run the existing exact candidate PG15/Redis7 Python3.11–3.13,
Ruff, Pyright, Node22/Vite, bcrypt, schema, structure plus Chrome
E2E workflow before independent WEB_INLINE IR012 on the exact
commit/tree. Only a **new, exact independent 0F/0A review** and all
competent preconditions permit applying the user's conditional
acceptance/integration authorization; never transfer a PASS from
another candidate or silently accept residual risk. No destructive
DB, real Redis, credentials, dependency update or staging deployment.

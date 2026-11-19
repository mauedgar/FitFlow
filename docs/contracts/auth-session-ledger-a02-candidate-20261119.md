---
document_id: FF-ISSUE108-A02-PGSESSION-CANDIDATE-20261119-001
status: candidate_not_accepted
issue: 108
baseline: PR116@9369f4cbf1ba767a73dd3bad835b1668cef19210
integration: false
---

# PostgreSQL durable session ledger — isolated Phase 1

Developer approved authoritative PostgreSQL session state and a bounded
legacy transition preserving original expiry, with reauthentication at cutover.
This FIRST candidate provides ORM, empty Alembic migration and transactional
CRUD + disposable tests. **Public login, refresh, bearer guards and logout are
NOT YET CONNECTED**, so full A02 revocation is NOT IMPLEMENTED/ACCEPTED.

The new table stores a random signed UUID4 family ID, authenticated user UUID,
SHA256 refresh credential digest, original expires_at, created_at, revoked_at.
No JWT secret or bearer raw value is persisted. PostgreSQL row locking
serializes the durable revoked_at COMMIT; retry of the same signed refresh
returns ALREADY_COMMITTED. Missing, stale, wrong-owner or wrong-digest claims
fail closed. Redis is not the persistence authority.

Source migration has never been run against retained data; Alembic upgrade,
rollback and tests are authorized **ONLY** on disposable fitflow_test DB.
Downgrade destroys the new table, not approved for any retained environment.
Existing JWTs without signed SID cannot be retrospectively assigned a login
family. Never claim their per-session revocation; preserve signed expiry and
require explicit reauthentication by documented cutover. No bulk invalidation.

Next gates: wire auth HTTP and both guards, verify PostgreSQL restart,
concurrent refresh/logout, lost ACK, old-client handling, no false HTTP 204,
independent whole-source security IR, distinct Product acceptance and
nonforced merge. No production, secrets, rulesets, retained DB, deploy or
changes to upstream PR114/116 in this commit.



## Phase 2 opt-in API and bearer guard candidate (not accepted)

Modern opt-in endpoints are `POST /auth/session/token`,
`POST /auth/session/refresh`, `POST /auth/session/logout`.
The new login commits a signed UUID4 family row before releasing JWTs.
Both existing bearer guard paths consult PostgreSQL for any JWT containing
`sid`; absence, wrong owner, expiry or durable revocation denies access
independently of Redis. Modern refresh verifies its signed refresh digest and
current active PostgreSQL account role. Modern logout accepts possession
of the exact signed refresh without requiring unexpired access bearer,
revokes with SELECT FOR UPDATE + COMMIT, and accepts exact idempotent replay.

The old /auth/token, /auth/refresh, /auth/logout paths remain in place
for SID-less legacy credentials through original JWT expiry. They are NOT
represented as durable session-family endpoints. New clients must explicitly
adopt modern endpoints and reauthenticate after the bounded legacy period.
Until frontend integration and the sunset ruling are reviewed, global login,
refresh and logout remain in transition. Redis cannot override a revoked
modern session. Failures before confirmed PostgreSQL COMMIT must not return
204. No live migration, production, secrets or user tokens were altered.


## IR001 F02 successor — controlled unknown transaction outcome

The independent IR001 at older HEAD 30a2a6bd33ed37c51d1cfbb5cb29e602f3155038
was NO_RECOMMEND with F01 legacy issuance and F02 uncertain commit error
contracts, plus five advisories. Its ORIGINAL remains unchanged. This
successor catches unexpected registration and logout transaction exceptions,
cleans up registration transaction state on any ordinary exception and
returns HTTP 503 without any credentials / without false 204. Tests now
inject failures **after an actual durable COMMIT** and show the first
response is UNCONFIRMED (503), while an exact signed refresh replay after
new DB connection returns the prior durable revocation ACK (204). Database
failure never implies re-running SQL writes blindly. Orphan modern sessions
after lost login ACK expire naturally without a bearer reaching clients.

**F01 remains OPEN:** legacy /auth/token still issues SID-less credentials,
and the frontend still uses that route. No silent cutover or source-only
assertion that all real users already use PostgreSQL sessions. A coordinated
frontend and legacy-issuance sunset, with original-expiry compatibility and
explicit reauthentication, is required before Product acceptance.

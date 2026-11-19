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

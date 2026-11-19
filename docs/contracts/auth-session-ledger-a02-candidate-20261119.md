---
document_id: FF-ISSUE108-A02-PGSESSION-CANDIDATE-20261119-001
status: candidate_not_accepted
issue: 108
baseline: develop@276481de41f6829e8dd7beed79127e13237b5dcb
integration: false
---

# PostgreSQL durable sessions — composed PR118 candidate, not deployed

The former Phase-1 statement that HTTP/guards were NOT connected is
HISTORICAL. Current PR118 implements PostgreSQL AuthSession registration for
every new login in /auth/token, /auth/session/token, and /auth/browser/token.
Frontend uses the browser HttpOnly refresh flow with memory-only access.

One signed UUID4 SID corresponds to one owner UUID, SHA256 refresh digest
(not raw JWT), expiry and revoked_at. PostgreSQL registration COMMIT
precedes releasing JWTs; uncertain COMMIT returns 503 without issuing any
credential. Modern access/refresh guards consult the persisted session and
current active/nondeleted User role and deny wrong-sub, expired, revoked
or missing family. Redis cannot override this authority.

Durable logout uses SELECT FOR UPDATE per session, revokes with COMMIT
and returns 204 only for a committed result or exact signed idempotent
replay. Failed/ambiguous transaction returns 503. Browser logout pending
holds the HttpOnly refresh cookie and recovery proof across lost HTTP ACK;
the browser must not replace the signed cookie until the exact revocation
replay clears it. A POST /auth/browser/refresh after PG commit cannot revive
the revoked session.

Existing signed SID-less tokens cannot be retrospectively assigned a
cryptographically certain session family. Legacy registered refresh may
mint bounded access until its ORIGINAL refresh expiration; after expiry,
reauthenticate. Already-issued SID-less access may remain live until its
signed exp after logout. That residual compatibility window is disclosed,
not misrepresented as immediate family-wide logout. No password reset or
subject-wide mass invalidation is performed.

Alembic a6b7c8d9e0f1 creates an initially empty auth_sessions table with
FK owner and scoped digest. Its DOWNGRADE destroys this table and may run
only on disposable fitflow_test; retention migration is NOT AUTHORIZED/RUN.
CI has disposable PG15 Redis7 and Python3.15.2, but exact final-HEAD
full independent review and production CORS/HTTPS topology remain pending.
No Product integration, staging, production or secret effects are presumed.

Earlier IR001 on fd376... found 5F/7A aggregate, prompting scoped repairs;
its original reviews and results are preserved unchanged. Final 0F0A
and all normal GitHub protections are required for merge.

## Control 015 — original API logout URL is now PG-backed (candidate)

The original POST /auth/logout has no Redis state transition. It requires
a signed refresh with SID plus an authorized owner bearer, and delegates
to PostgreSQL revocation; failed COMMIT/ACK never returns false 204.
Use /auth/session/logout for replay when an access bearer has expired or
was revoked. Legacy SID-less bearer acceptance is not yet removed.

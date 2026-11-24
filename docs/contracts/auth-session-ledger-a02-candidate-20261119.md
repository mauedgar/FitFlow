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
cryptographically certain PostgreSQL session family. Current HTTP refresh
rejects all SID-less tokens even with historical Redis registration, and
current bearer guards reject signed SID-less/untyped access regardless of
remaining cryptographic expiry. Historical tokens may still be signed until
exp, but they are not accepted as modern access. Reauthentication is
required; no password reset or subject-wide mass invalidation is implied.

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
was revoked. Signed SID-less bearer acceptance was removed in this PR118 candidate;
only typed PostgreSQL-registered SID families can authorize requests.

## Control 015 — expiry-boundary replay and session ownership

Independent IR003 identified a missing expiry-boundary ACK. The ledger
now parses a signed refresh with expiration ignored only in its exact
replay path; an active session must still have both unexpired signed JWT
and ledger row. After commit and loss of ACK, the same already-revoked
family may acknowledge 204 even if the refresh JWT expires before retry.
An expired token cannot revoke any row which is not already revoked.
Disposable PostgreSQL unit/HTTP tests cover exact committed replay,
expired unrevoked rejection and spoofed subject rejection.

Standalone auth_service no longer opens an async FastAPI dependency
without closing it: the caller must inject/own the AsyncSession.
Test-only family helper requires localhost plus test profile and
fitflow_test, not database name alone; fixture teardown remains an
independent review concern, and this is not a claim of production safety.

## Control 015 — IR004 refresh/logout PG row lock (candidate)

Both /auth/session/refresh and /auth/browser/refresh now obtain an
exclusive SELECT FOR UPDATE on the exact session-family row before
reading persisted user role and issuing access. A logout must acquire
that same lock and COMMIT; it cannot overtake an in-progress refresh.
Ordinary bearer verification and cookie session rehydrate remain
nonlocking to avoid serializing normal reads. A disposable real
PostgreSQL NOWAIT regression witnesses the lock boundary and its release.
Source and tests remain subject to new exact-commit CI and IR.


## IR018 S02 repair — strict durable claim boundary (candidate)

Durable register, refresh, activity and replay require canonical owner UUID,
UUID4 SID and explicit refresh purpose for refresh credentials. Historical
registry helpers are not modern HTTP authority. NumericDate must represent
an actual UTC instant; nonfinite and out-of-range values fail closed. The
refresh path rechecks signed expiration after row-lock acquisition. A corrupt
nonhex or non-ASCII persisted digest is denied, including bearer-only checks;
this is a runtime validation, not a new schema constraint or retained-data
migration. Rollback cleanup does not replace the original transaction error.
Configuration rejects nonpositive JWT lifetimes. No unreviewed release or
migration authority follows from this candidate.

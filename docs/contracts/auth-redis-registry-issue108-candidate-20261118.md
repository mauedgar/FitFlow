---
document_id: FF-ISSUE108-REDIS-REGISTRY-20261118-001
status: candidate_not_accepted
issue: 108
baseline: develop@276481de41f6829e8dd7beed79127e13237b5dcb
integration: false
---

# Redis registry A01 and modern durable revocation A02 — PR118

This is the CURRENT composed candidate, not the original pre-repair PR114 or
PR116 snapshot. Earlier scoped independent IRs remain historical.

Redis token_store requires signed purpose, subject and live exp; it compares
persisted registration owner against JWT sub (never mere key existence).
New registrations use opaque SHA256-derived key names and an absolute Redis
EXAT cutoff at floor(signed exp), with application and Redis wall clocks
assumed synchronized. The cutoff is not extended by client/ping/SET latency;
near-expiry registration is rejected rather than rounded up. Owner comparison
uses UTF-8 bytes, rejects invalid encodings and rechecks live expiry after
lookup. Mismatched opaque owners fail closed without fallback to old raw
keys. Historical SID-less raw registrations are never created or rewritten;
explicit exact-token deletion can remove both opaque and historical keys.
Existing raw-key/blacklist remnants may outlive
their token expiry and require separate authorized retained keyspace
inventory/sunset, never an implicit bulk cleanup.

Modern signed SID registration and revocation ARE IMPLEMENTED in current
unmerged PR118 code: PostgreSQL AuthSession owns registration, durable
row-locked revoked_at and exact idempotent replay. Redis is not a security
authority for modern login, refresh, bearer guards or logout. A revoked
modern family stays denied after Redis cache loss or restart.

Historical SID-less refresh registration and blacklist keys may still be
present in Redis, but the current /auth/refresh and /auth/session/refresh
endpoints never consult them to mint access. No SID-less access is issued.
The current bearer gates also reject old SID-less and untyped access tokens
regardless of their original signed exp. Cryptographically old artifacts may
exist until expiry, without an HTTP authorization path or retroactive SID
family assignment. Retained Redis cleanup needs separate authorization;
do not infer a subject-wide revocation or delete keys implicitly.

No retained Redis/PostgreSQL writes, credentials, secret updates, staging,
production or migration were performed. Current code/tests/doc are
candidate-only, requiring full exact-HEAD 0F0A independent review and
authorized nonforced merge.

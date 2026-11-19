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
New registrations use opaque SHA256-derived key names and signed-exp-bounded
positive TTL. Mismatched opaque owners fail closed without fallback to old
raw keys. Historical SID-less raw registration keys are read-only and not
automatically rewritten. Existing raw-key/blacklist remnants may outlive
their token expiry and require separate authorized retained keyspace
inventory/sunset, never an implicit bulk cleanup.

Modern signed SID registration and revocation ARE IMPLEMENTED in current
unmerged PR118 code: PostgreSQL AuthSession owns registration, durable
row-locked revoked_at and exact idempotent replay. Redis is not a security
authority for modern login, refresh, bearer guards or logout. A revoked
modern family stays denied after Redis cache loss or restart.

Historical SID-less refresh remains validated through Redis registration/
blacklist and may mint only expiry-CAPPED SID-less access. A legacy refresh
logout does not revoke every already-issued access credential of that user;
signed legacy access may remain until original exp. No retroactive family
assignment or blanket subject-wide revocation is claimed. This compatibility
boundary is NOT equivalent to modern durable logout.

No retained Redis/PostgreSQL writes, credentials, secret updates, staging,
production or migration were performed. Current code/tests/doc are
candidate-only, requiring full exact-HEAD 0F0A independent review and
authorized nonforced merge.

---
document_id: FF-ISSUE108-JWT-PURPOSE-ISOLATED-20261118-001
status: candidate_not_accepted
issue: 108
baseline: develop@276481de41f6829e8dd7beed79127e13237b5dcb
integration: false
---

# JWT purpose boundary: composed current PR118 candidate

The original PR114-only source and its independent NO_RECOMMEND reports are
IMMUTABLE HISTORICAL EVIDENCE. The current source is the composed PR118
candidate, not an assertion that the inherited Redis bug remains unfixed.

All newly issued JWTs contain signed, non-overridable token_use access or
refresh. Refresh JWTs discard any role claim. Both bearer guards reject
refresh-as-access, including untyped legacy refresh. Access cannot be
refresh/logout proof. Invalid purpose, subject or expiration fail closed.
Historically, signed untyped access had a role and original expiry, while
untyped refresh was role-free. Those are historical format observations:
the current bearer and refresh endpoints reject untyped and SID-less tokens,
regardless of whether the cryptographic signature is still unexpired.

All new logins through /auth/token, /auth/session/token and
/auth/browser/token establish signed UUID4 SID families in PostgreSQL before
emitting credentials. Modern refresh/logout and both guards consult
PostgreSQL persistent session state; Redis cannot revive a revoked SID.
Refresh and roles use the current, active, nondeleted persisted User.

The original A01 Redis owner-binding issue is REPAIRED in source: signed
refresh sub must match stored Redis owner, opaque new registration keys are
SHA256-derived and expire within signed JWT exp, mismatched opaque entries
never fall back to raw legacy keys. Historical raw Redis records remain
read-only compatibility and are not automatically deleted.

Current PR118 /auth/refresh and /auth/session/refresh reject all signed
SID-less refresh: historical Redis registration/blacklist is not an active
HTTP compatibility route, and NO new SID-less access is issued. The current
bearer guards reject both untyped access and SID-less access regardless of
remaining cryptographic exp. No retrospective SID family is manufactured
for an old token. A historical signed token may still exist until its exp,
but this is not current bearer authorization or a revocation guarantee.
Any residual Redis key cleanup is a separate retained-data decision.

Old IR findings and advisories remain unchanged. Exact final source
needs fresh 0F0A independent review, PG15/Redis7/CPython3.15.2 native CI
and Developer Product acceptance. No retained migration, staging, secret
rotation, production or merge is implied by this documentation.

## Control 015 — successor refresh gate (candidate, not merged)

Original /auth/refresh now delegates exclusively to the PostgreSQL session
ledger after a signed SID check, without Redis fallback or SID-less issuance.
The original /auth/logout alias requires a modern SID-backed refresh and
authenticated owner bearer; both bearer guards reject SID-less tokens.
Native CI and independent review on exact successor SHA remain mandatory.

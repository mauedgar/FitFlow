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
Untyped historical access requires a signed role and original exp; untyped
historical refresh must omit role and have a live original exp.

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

Existing signed SID-less refresh, with authentic historical registration
and no blacklist, may issue another SID-less access with expiration capped
to the ORIGINAL signed refresh expiry. No manufactured SID family is
attributed to these tokens. Legacy logout cannot instantly invalidate all
already-issued SID-less access: those tokens live until their signed exp.
This bounded residual is explicit and needs Product risk disposition before
the global 0F0A gate; do not disguise it as modern durable revocation.

Old IR findings and advisories remain unchanged. Exact final source
needs fresh 0F0A independent review, PG15/Redis7/CPython3.15.2 native CI
and Developer Product acceptance. No retained migration, staging, secret
rotation, production or merge is implied by this documentation.

## Control 015 — successor refresh gate (candidate, not merged)

Original /auth/refresh now delegates exclusively to the PostgreSQL session
ledger after a signed SID check, without Redis fallback or SID-less issuance.
Existing /auth/logout legacy and bearer SID-less authorization are not yet
retired. Native CI and independent review on exact successor SHA required.

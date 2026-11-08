---
document_id: FF-ISSUE108-JWT-PURPOSE-20261108-001
status: review_required
issue: 108
candidate_pr: 107
acceptance: false
integration: false
---

# JWT purpose isolation: candidate contract, not accepted

A02 security repair is serialized into PR #107 alongside Issues #43/#44, under the explicit developer expansion for Issue #108. This does not import authority from any other project.

New access tokens are signed with `token_use: access`, refresh tokens with `token_use: refresh`. Emitters override a caller's purpose, and refresh never contains role. Both bearer guards reject any refresh-purpose JWT. Refresh/logout handlers reject access-purpose JWT.

Legacy untyped access JWTs remain usable only with a signed nonempty role claim and original valid expiry. Legacy untyped refresh JWTs have no role and remain eligible solely at refresh/logout under existing Redis registration and blacklist semantics. Unknown or mismatched explicit purpose fails closed. Database role remains authoritative for permissions. No existing tokens, hashes, users or retained state are rewritten.

Tests on exclusively disposable PostgreSQL15/Redis7 cover real HTTP bearer denial, login identity compatibility, legacy and typed refresh, logout, blacklist reuse denial, invalid purpose, and forged role authorization. Existing accepted contracts must not regress. No staging/deploy, credential changes or runtime authorization from this document.

Full candidate CI, source review and independent FULL PRODUCT IR at **0 findings/0 advisories** remain mandatory. A01 ruleset repair is a separate guarded operation before any eventual non-forced integration, after explicit Product acceptance.

## IR002 F001: refresh role continuity

The refresh endpoint must resolve the signed subject as a UUID, load the active, non-soft-deleted user from PostgreSQL and sign a new access JWT with that user's **current persisted role**, never a caller-supplied or stale refresh-token role. An inactive, deleted, missing or malformed subject fails closed without issuing a token. The refresh credential still must pass Redis registration and blacklist checks. Synthetic real-HTTP tests verify role continuity across refresh and changed current roles, as well as negative inactive/missing subjects; no retained data is touched. This is a candidate repair, not acceptance of the IR002 finding or Product integration. Historical refresh-minted untyped access tokens lacking role cannot be safely differentiated from legacy refresh credentials and remain denied as bearers; clients must reauthenticate.

## Candidate Redis retention

New refresh-token registrations and new blacklist records use a positive Redis expiry bounded by the cryptographically verified JWT `exp`, rounded up to avoid premature removal. Malformed/expired JWTs cannot generate an unbounded key. This change does **not** migrate or delete any pre-existing retained Redis keys without a separately authorized cleanup procedure; prior records may remain until operational reconciliation. HTTP integration on disposable Redis7 asserts positive TTL for both registration and revocation, and tests assert rejection of malformed expiry. No production Redis access is authorized.

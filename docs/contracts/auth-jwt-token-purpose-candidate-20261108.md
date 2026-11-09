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

## Frontend JWT claim interpretation — review-required

The React session context now performs an **untrusted local UX check** on JWT expiry, access purpose, subject and supported role before hydrating session state, including legacy untyped access. This is not a cryptographic signature validation and cannot authorize any API action: the backend's signed JWT, active-account and database-role guards remain authoritative. Redis/refresh JWT must never be presented as a local access identity. Signed teacher roles match the backend `teacher` value; historical frontend `trainer` display references are retained until separately reviewed. The decoded `sub` is a UUID and not proof of the user's email; the existing UI profile model still needs separate server-side identity projection if email is shown.

## IR003 F001: authoritative frontend identity

The JWT signed `sub` is a UUID **not an email address**. AuthProvider must treat its locally decoded claims as untrusted UX prechecks only, then use the existing authenticated `GET /auth/me` response to project `currentUser.id`, `currentUser.email`, `currentUser.role` and `currentUser.active`. The returned ID must equal the local JWT subject; disabled/malformed/mismatched profiles and backend errors must fail closed rather than fabricating identity. The ADMIN session gate and query cache key must compare authenticated UUID to the server identity UUID, not email. No new API, database migration, credential or retained state change is permitted. Synthetic client-side projection tests cover UUID/email separation, current role and negative malformed data; the signed browser ADMIN E2E must remain green.

## IR003 Redis key privacy repair

All **new** JWT registration and blacklist Redis keys use deterministic SHA-256 digest identifiers, with the original signed JWT never placed in the key name; existing positive expiry bounded by signed JWT `exp` remains unchanged. The code supports read-only fallback for legacy raw JWT keys to avoid silently invalidating already issued refresh credentials, and explicit logout deletes the identified credential in either supported format. No bulk migration, scan, deletion or mutation of historical retained keys is authorized; a future isolated operational cleanup requires a separate Product disposition. Synthetic unit and disposable HTTP/Redis tests prove opaque new keys, TTL, legacy lookup and logout compatibility. This is not a claim that all historical Redis storage risk has been eliminated.

## IR004 F001 — single validated TanStack Query factory

The shared React identity cache key must be paired with one shared **validated query function**. Both `AuthProvider` and `useAdminIdentity` now consume `verifiedAuthIdentityQuery(token, sessionGeneration)`. This factory checks the untrusted JWT for UX only, performs exactly one authenticated `/auth/me` request and passes the server response through `projectServerAuthUser` (same subject ID, authoritative email/current role, active account). ADMIN must never reuse raw API response data under the validated profile cache key. The real backend remains responsible for JWT signature and authorization. No Product acceptance is implied until CI and new independent review on the successor tree.

## A03 — signed per-login session revocation (proposed in successor)

Each new login emits an access+refresh JWT pair containing one cryptographically signed UUID4 `sid`. Refresh preserves that `sid`; both authorization pipelines check Redis for the hashed session revocation marker and individual token blacklist, failing closed with HTTP 503 when Redis is unavailable. Logout requires valid bearer and matching refresh `sub` and `sid`, writes a session revocation marker with positive TTL no shorter than refresh expiry **before** deleting/blacklisting refresh, and invalidates all already issued access JWTs of that session. A mismatched session cannot revoke another credential. Historical JWTs without `sid` retain their original expiry for bounded compatibility; logout explicitly blacklists the presented historical access JWT, but previously minted uncorrelated historical access JWTs cannot be revoked as a family and may require fresh login. No retained Redis keys are scanned, deleted in bulk or migrated. The SPA holds refresh in tab-scoped sessionStorage and clears local state even if remote logout fails, reporting revocation as unconfirmed rather than claiming success. This is a candidate security contract subject to synthetic PG15/Redis7 and browser E2E plus independent full review; no Product acceptance or deployment is implied.

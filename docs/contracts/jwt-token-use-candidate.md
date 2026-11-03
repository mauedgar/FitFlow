---
document_id: FF-ISSUE54-IR003-JWT-TOKEN-USE-20261102-001
status: review_required
date: 2026-11-02
source: https://github.com/mauedgar/FitFlow/pull/54#issuecomment-6585366073
developer_authority: explicitly_authorized_f04_a01_a02
product_acceptance: not_granted
merge_authorized: false
---

# JWT access/refresh classification — candidate and DocImpact

IR003 identified that an untyped, unexpired refresh JWT could be accepted
as Bearer on protected endpoints, even after logout. The old issuer signed
access and refresh with the same key and no type discriminator.

## Candidate security contract

- New access JWTs carry signed `token_use=access`; ONLY this type is
  accepted by `get_current_user` and `get_user_from_token` / role guards.
- New refresh JWTs carry signed `token_use=refresh`, without role.
- `/auth/refresh` requires signed/unexpired refresh-purpose JWT and Redis
  registration, with blacklist rejection. Historical refresh JWTs lacking
  `token_use` AND `role` retain refresh ability **only** while their exact
  token is registered and not blacklisted in Redis; they never authenticate
  as Bearer and are not reissued as legacy tokens.
- `/auth/logout` requires an access Bearer JWT for the same subject and
  a correctly typed/legacy refresh token to revoke; it preserves the
  existing Redis delete-then-blacklist transition and 204/400/403/503
  behavior. Logout remains refresh revocation, not immediate access JWT
  revocation (access expires after default 30 minutes).
- Untyped historical access JWTs can no longer be used as Bearer, as they
  cannot be reliably distinguished from legacy refresh credentials. Users
  may redeem an active registered refresh token to obtain typed access,
  or log in again. Deliberate migration/security boundary; no silent
  acceptance of an untyped Bearer token.
- `decode_token` stays a generic signature/expiry decoder; contextual
  authorization must verify `token_use`. A caller cannot override the
  issuer's signed purpose field.
- No new JWT keys, external credentials, migrations, dependencies,
  or production data operations. No changes to public registration
  semantics; duplicate email includes HTTP 400.

## Evidence requirements

Disposable Postgres 15 + Redis 7 full HTTP checks: real logout and
revocation; refresh cannot be Bearer before/after logout; typed access
cannot refresh/logout as credential; registered legacy refresh can
renew and be revoked; unregistered legacy refresh cannot renew.
IR003 A01 adds negative role/spoof/soft-deleted/nonexistent tests.
Full backend Python 3.11/3.12/3.13, Ruff, Pyright, frontend,
bcrypt and schema checks must be against the new SHA/tree; independent
IR004 is required for an acceptance proposal. No automatic merge/close,
Issue37 staging/E2E remains NOT_RUN.


## IR004 follow-up — role, unique refresh, Redis TTL, inactive state, rotation

Read-only IR004 source: https://github.com/mauedgar/FitFlow/pull/55#issuecomment-6586129538.
This successor addresses F05/F06 and A03/A04/A05 under the developer's
authorization to continue the next competent dependency. It remains a
review-required candidate and has no Product acceptance or merge authority.

- **F05:** Refresh now verifies the current account by UUID in the ORM,
  rejects missing/soft-deleted/disabled principals, and returns a typed
  access JWT with current persisted `role` alongside `sub`. The frontend
  `AuthProvider` reads role from the access JWT to enable navigation;
  authorization on the server remains controlled by the ORM role and
  does not rely on the caller-supplied role claim.
- **F06:** A cryptographically random UUID4 `jti` is signed into **every
  newly issued refresh JWT**, even when multiple logins occur in the same
  NumericDate second. Two sessions no longer share an exact Redis key
  or blacklist fate; legacy refresh JWTs without `jti` are supported
  only while they are still signed, live and registered in Redis.
- **A03:** Refresh store and blacklist write Redis `SET EX` using the
  remaining signed `exp` lifetime, not indefinite retention. This
  applies to typed and legacy refresh tokens. Existing historical Redis
  entries without TTL are untouched (no destructive production cleanup)
  and are still checked against the signed JWT expiry. Token strings
  remain key material for backward compatibility; new Redis key
  naming/hash migration is explicitly **not** assumed in this candidate.
- **A04:** `REFRESH_TOKEN_ROTATION=False` is now the real default.
  Starting a runtime with `REFRESH_TOKEN_ROTATION=True` is explicitly
  rejected during configuration validation. The current
  `POST /auth/refresh` contract returns **only** `access_token`
  and `token_type`; the frontend does not store/replace a rotated
  refresh credential. Atomic rotation, replay policy and client
  migration require a separately versioned Product contract rather
  than silently breaking existing consumers. Repeated renewal of a
  registered live refresh remains supported until logout/expiry.
- **A05:** Inactive users cannot log in even with correct credentials,
  nor redeem an otherwise registered refresh token; disabled and
  soft-deleted users fail refresh 401, without identifiers in the
  response. Existing tokens are not erased from Redis en masse:
  protected accesses already reject inactive accounts, and token
  expiry/revocation remain bounded to signed TTL.

Real HTTP/PG15/Redis7 tests on synthetic user/token keys prove
refresh-to-client role, deterministic same-second login→logout→login
and independent renewal, Redis TTL after registration/revocation,
inactive login and refresh, soft-deleted refresh and startup rejection
of unsupported rotation. No schema, dependency, frontend, staging
or external-credential edits were made. Full CI must qualify the
exact successor SHA/tree and a **new independent IR005** must return
zero findings and advisories before recommending candidate acceptance.
Issue37 deployed E2E remains NOT_RUN.

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

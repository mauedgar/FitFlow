---
document_id: FF-ISSUE53-PRIVACY-CONTRACT-20261102-001
status: review_required
date: 2026-11-02
developer_authority: scoped_api_privacy_repair_authorized
product_acceptance: not_granted
merge_authorized: false
---

# FitFlow · Privacy policy for user-account read endpoints — candidate

## Decision and scope

Developer authorized resolving [PR53 IR002 F03](https://github.com/mauedgar/FitFlow/pull/53#issuecomment-6583921532)
and delegated the public API contract decision to FitFlow Control. This document
specifies a candidate, **not** final integration or acceptance.

The existing `UserPublic` DTO contains `id`, `email`, `role`, `active`.
Those are sensitive account fields, not an anonymous member-directory projection.
The historical `/users/public` route name is preserved for routing compatibility,
but it no longer implies anonymous access. No separate public directory is introduced.

| API v1 | Authentication / authorization | Success / failure |
| --- | --- | --- |
| `POST /users/register` | Anonymous; only `client` role persisted | 201 / **400** duplicate email (including UNIQUE race) / 422 |
| `GET /users/public` | Bearer token + real ORM `admin` role | 200 list / 401 / 403 |
| `GET /users/{user_id}/public` | Bearer token + ORM `admin` or account owner | 200 / 401 / 403 / 404 |
| `GET /users/me`, `GET /users/me/stats` | Authenticated JWT owner only | unchanged |
| `GET /auth/me` | Authenticated JWT owner only | unchanged |

The directory retains the existing paginated-by-CRUD default and soft-deletion
filtering; no new search/filter/export capability. The individual route returns
403 to a non-owner even if the target UUID is nonexistent (no existence oracle);
admins see 404 for nonexistent/soft-deleted accounts. Role is checked from the
database-backed authenticated principal, not from an unverified role claim.
Unauthorized responses never contain account names/emails/roles.

## Compatibility assessment

- No identified frontend caller of `/users/public` or `/{user_id}/public`.
  Existing login, registration, owner profile and admin fixtures remain unchanged.
- The change is intentionally security-breaking for anonymous third-party
  consumers. A future public member directory, if product-approved, needs a
  separate minimal projection, opt-in and independent privacy review.
- `UserPublic` continues to contain email/role only behind the accepted owner
  and administrator boundaries. It is **not** an anonymous response model.
- The route names are historical; a later versioned rename can be considered,
  but no alias or additional exposure is created in this candidate.
- Database schema, migrations, passwords, bcrypt, dependency lock, billing,
  staging and external identities remain untouched.

## Validation and unresolved gates

The candidate must be verified against its own immutable SHA/tree with full
backend PG15/Redis7/Python 3.11–3.13, Ruff, Pyright, frontend and bcrypt
compatibility where applicable. New integration HTTP tests cover 401/403/200/404
using disposable synthetic users and signed JWTs; no real user data.

An independent WEB_INLINE IR003 is required on the *new exact commit/tree*.
Only 0 findings / 0 advisories permits an acceptance recommendation; approval
and merge remain separate explicit Developer gates. Issue37 deployed staging
and E2E remain NOT_RUN. PR53 prior IR002 never transfers to this candidate.

## IR003 follow-up

IR003 F04 (JWT refresh-as-Bearer) and A01/A02 are addressed by a distinct
successor candidate. Access Bearer requires signed `token_use=access`;
renewal permits typed or still-Redis-registered legacy refresh tokens only.
Legacy untyped access tokens intentionally require renewal or fresh login.
See `jwt-token-use-candidate.md`. No change to user privacy routing/pagination.

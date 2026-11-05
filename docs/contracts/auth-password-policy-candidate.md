# FitFlow Issue #43 — proposed public password contract (NOT ACCEPTED)

Status: Product candidate under Issue #43 policy ruling, not integrated. Source of authority: Issue #43 comment 6582023324, canonical develop c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d and SOURCE_OF_TRUTH v5.3. This is an intentional **material API behavior change** compared with legacy Passlib, not a semantics-preserving dependency-only upgrade.

## Account creation (public HTTP)

- POST /api/v1/users/register accepts a new password of **at most 72 UTF-8 bytes**, with **no NUL**. Byte length is not character count: 36 instances of ñ are 72 bytes, 37 are 74. Exactly 72 bytes are allowed; empty passwords remain allowed by the current schema (a separate minimum-strength policy is out of scope).
- Passwords above 72 UTF-8 bytes or containing NUL return HTTP **422** with the FastAPI/Pydantic validation detail array identifying body.password. This happens before any user lookup, CRUD or hash creation. Legacy creation previously accepted overlong input with silent bcrypt truncation. Do not describe the transition as unchanged behavior.
- A successful valid registration returns 201 and the existing UserPublic shape; duplicate email still returns 400. No changes to stored hash column or JWT format.
- The current React registration screen displays the 72-byte UTF-8 limit, and its API client translates a password-field 422 into a safe actionable Spanish error. It does not log passwords or expose raw validation objects.

## Existing users and recovery

- POST /api/v1/auth/token continues to verify existing bcrypt $2a$, $2b$ and $2y$ hashes, including legacy passwords exceeding 72 bytes (bcrypt compares only the first 72 bytes). A malformed, invalid-cost or non-ASCII stored hash fails authentication with HTTP 401, not 500. Login does not automatically rehash or rewrite the stored hash.
- Exactly-72-byte new bcrypt hashes **also** accept a submitted password with an appended suffix: this is inherited bcrypt verification aliasing, including multi-byte UTF-8 input, not a promise of full-string comparison. New creation does not truncate; verification must preserve legacy compatibility until a separately authorized migration decision.
- No forced password reset, bulk rehash, real-user lookup, schema migration or credential changes. An existing user can keep signing in with the old password. A voluntary password change, when a separately exposed and authorized recovery/update flow is available, must follow the new 72-byte/NUL policy; users with longer legacy passwords would need to choose a compliant new password. Do not claim a public reset/change endpoint exists today.

## Update-route qualification

- UserUpdate validates password with the same rules for internal CRUD use, but there is **no public user password update route** in this candidate. The mounted backend/app/routers/users.py defines POST /register and GET /public, /{user_id}/public, /me, /me/stats; no PUT/PATCH for users. backend/app/api/v1/api.py includes that router and the remaining domain routers have no UserUpdate password endpoint. Therefore an HTTP update 422 test is **N/A**, not a simulated endpoint or claimed public behavior.
- A unit-level UserUpdate negative test proves invalid updates are rejected before CRUD; a route inventory regression asserts no public PUT/PATCH /users route is accidentally claimed. Introducing password recovery or an update API requires its own authorization and tests.

## Acceptance and integration

- New candidate must pass synthetic old Passlib 1.7.4/bcrypt 3.2.2 -> native bcrypt 4.3.0 and native bcrypt 4.3.0 -> isolated legacy Passlib verification, including Unicode, 72-byte boundary, wrong passwords, and no rehash.
- PR #46 changes Python/dependency locks; PR #48 changes auth typing/security/schema and broad quality surfaces. Neither is integrated or implicitly covered by PR #51 CI. Integrate only after Developer grants an order, rebase/reconcile without force, regenerate lock/exports with uv 0.13.6 if dependencies change, rerun combined exact-SHA tests and independent review.
- PR #51 stays DRAFT, Issue #43 OPEN. Independent 0 findings / 0 advisories and later Developer acceptance are mandatory before integration.

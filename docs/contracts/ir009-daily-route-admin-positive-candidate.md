---
document_id: FF-IR009-REMEDIATION-20261102-001
status: review_required
source: https://github.com/mauedgar/FitFlow/pull/60#issuecomment-6593323944
authority: user_authorized_repair_and_IR_loop
product_acceptance: false
merge_authorized: false
---

# IR009 successor — static daily route and positive admin mutation evidence

## Frozen predecessor and authority
Independent WEB_INLINE IR009 on PR60 commit
`daa23d75ad8fa5c5d0337d4e9ad8ec4e10df4e90` / tree
`b5a59de84182070c9acea5a2f5c6596be1784f4c` returned
NO_RECOMMEND, F21 MEDIUM and 7 advisories (A10/A11/A12 MEDIUM;
A13/A16/A17/A18 LOW). An earlier IR009 attempt was BLOCKED with
no receipt; the completed independent receipt was published once after
direct commit/tree verification. Do not interpret a repaired candidate
or CI result as Product acceptance, integration or close authority.

## F21: static `GET /class-sessions/day` not shadowed

The static route is registered *before* `GET /class-sessions/{session_id}`.
FastAPI/Starlette therefore routes `day` to the daily handler instead
of passing it to UUID validation and returning unrelated 422.
The existing daily handler and date query contract are unchanged.
A new real HTTP PostgreSQL15 integration test uses synthetic
populated sessions at a stable UTC afternoon time, checks that
`GET /class-sessions/day?date_query=YYYY-MM-DD` responds 200 with
the expected session ID, and checks invalid date returns 422 from
the intended handler's query validation.

## A18: stronger positive authorization and ORM evidence

An additional real HTTP regression test with disposable synthetic
PostgreSQL users verifies an active admin can POST a valid GymClass,
then PUT it after a synthetic ClassSchedule is attached and read
its eagerly loaded nested relation, then DELETE it with soft-delete
and observe it absent from public detail. All synthetic rows are
deleted by test-owned IDs in a finally block.
Previously covered anonymous/non-admin 401/403 mutation tests and
populated catalog/schedule projections are retained.
This addresses part of A18; it **does not** replace the omitted browser
E2E, bcrypt reverse Passlib checks or independent unpack of the
schema archive, and does not justify silently removing the advisory.

## Residual decisions and evidence limits

A10: lost response after server-side refresh registration cannot be
compensated by a client that never received the token. Signed expiry
limits lifetime; server-side observability and delivery semantics
require explicit contract and operations consideration.

A11: actual mounted browser/deployed E2E remains **NOT_RUN**. Node
VM/TypeScript simulation is not browser proof. The open Issue37
concerns staging requalification; it is not by itself proof of
completed browser E2E.

A12: trusted reverse proxy identification, shared-IP behavior and
per-account lockout are deployment-policy issues; TESTING must remain
false in staging.

A13: legacy pre-jti refresh credentials still require raw Redis key
fallback, limited to their signed expiry. No bulk migration/deletion
or production Redis operations are authorized.

A16: teacher access to booking records is currently role-wide,
not scoped to assigned classes. Any restrictions require an
explicit Product privacy/role policy and compatible API tests.

A17: unauthenticated operational catalog and schedules responses
include broader metadata than their dedicated public projections.
Changing established response schemas may break frontend consumers;
Product should decide role-gating versus versioned projections.

A18: positive admin HTTP coverage added, but omitted E2E / reverse
Passlib / artifact unpack remain disclosed.

### Verification and handoff

Qualify the new SHA/tree using existing exact GitHub Actions matrix:
PG15+Redis7 Python3.11/3.12/3.13, Ruff, Pyright, Node22 tests and
Vite build, bcrypt, schema and structure.
An independent original WEB_INLINE IR010 must review the integrated
tree; 0 findings plus 0 advisories is required to *recommend*
Product acceptance. Do not auto-accept, merge, deploy or close issues.
No production DB/Redis, secrets, dependency changes, migrations
or destructive effects were used.

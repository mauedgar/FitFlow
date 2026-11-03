---
document_id: FF-IR008-REMEDIATION-20261102-001
status: review_required
source: https://github.com/mauedgar/FitFlow/pull/59#issuecomment-6592364347
authority: user_authorized_next_recommended_action
product_acceptance: false
merge_authorized: false
---

# IR008 successor — privacy, authenticated guards, session and ORM contracts

This frozen successor of PR #59 is a DRAFT Product candidate, not
acceptance, merge, or deployment authority. The exact SHA/tree will be
published by the candidate. Previous independent IR008 returned 5 findings
(1 HIGH, 4 MEDIUM) and 7 advisories, disposition NO_RECOMMEND.

## F16 — teacher directory and sensitive identity
The operational GET `/teachers/` directory, including every teacher's CUIL,
personal document, address and medical_fit_url, is restricted to ORM-backed
active administrators only. Teacher-owned private GET/PUT by profile UUID
remains bounded by Person.user_id owner check; `/teachers/public` remains
public and uses the safe TeacherPublic projection (not CUIL/medical fields).
Synthetic HTTP checks include a teacher denied access to the directory,
admin read of populated sensitive fields, and safe public response.

## F17 — per-client commercial membership privacy
GET `/memberships/client/{client_id}/public` now requires valid access
Bearer. Admin and operational front desk can see the requested history;
client role can see **only its own** profile history, resolved through the
persisted Client.user_id mapping. Teacher/anonymous/foreign client are
denied without proving another profile's existence. Client-specific plans,
commercial dates and activity are never available from this path to
anonymous callers, despite the legacy suffix `/public`.
No schema migrations or modifications to membership data.

## F18 — invalid Bearer on generic guards
`require_current_user` maps AuthError from the token and ORM authentication
service into HTTP 401 + WWW-Authenticate: Bearer, independent of whether the
Bearer is malformed, expired or has an unrecognized principal. A valid
authenticated but unauthorized role still receives HTTP 403. Synthetic
HTTP negatives cover malformed bearer on multiple guard families.

## F19 — schedule UUID, GymClass UUID and query parameters
`GET /class-sessions/class/{class_id}/public` passes gym_class_id to the
existing CRUD relationship join rather than treating class ID as a schedule
ID. The frontend `getClassSessions` sends `schedule_id`, `date_from`,
`date_to`, matching the API. The previously unsupported
`include_cancelled` query flag is now consumed: false excludes cancelled
sessions, true includes them. Absent flag retains historical read behavior.
Real PostgreSQL HTTP fixture creates a GymClass, a distinct ClassSchedule
UUID, active session and cancelled session; validates both filters,
time range and distinct UUID behavior.

## F20 — fully loaded ORM schedule and catalog projections
Operational schedule list serializes ClassScheduleWithRelations only after
eager loading gym_class, teacher and class_sessions, regardless of the
historical include_relations query toggle. GymClass filtered list eagerly
loads nested ClassSchedule.teacher and ClassSchedule itself. GymClass
detail and POST/PUT response use explicit loaded reload before schema
serialization, avoiding lazy="raise" 500s. The nested ClassSchedule schema
now represents `allowed_plan=None` (valid per ORM and business contract).
Populated HTTP fixtures confirm nonempty catalog and schedule response
and safe public GymClass projection. No ORM lazy setting is weakened.
Legacy include_schedules=false still returns the populated operational
nested schedule array; document this compatibility behavior rather than
suppressing it silently.

## Independent advisory inventory, not unearned closure
- A10 (lost login response/refresh orphan): signed TTL bounds token lifetime;
  no claim that client can revoke a token it never received.
- A11 (real browser or deployed E2E): still **NOT_RUN**; PG HTTP and
  Node VM suites cannot replace mounted Playwright tests, Issue37 remains.
- A12 (login limiter): staging TESTING bypass is blocked, but proxy/IP
  topology and intentional account-wide lockout remain operational policy.
- A13 (legacy raw JWT Redis keys): pre-jti compatibility is preserved;
  retirement needs a separate explicit production migration grant.
- A16 (booking privacy): operational reads remain role-wide, not teacher
  assignment-scoped; requires Product permission/visibility policy.
- A17 (public/operational read contracts): this candidate fixes source
  stability without silently changing public GET /gym-classes/ or
  GET /class-schedules/ response schemas. A decision about new safe
  read-only projections / versioning remains necessary.
- A18 (evidence gaps): the candidate adds populated ORM, JWT error and
  PII isolation real HTTP tests; administrator positive mutations and
  browser/legacy multi-Python reversibility require further confirmation.

### Gates and boundaries
Run immutable candidate CI in existing GitHub Actions: PostgreSQL15/Redis7,
Python3.11/12/13, Ruff, Pyright, frontend Node22+Vite, bcrypt,
schema and structure. Independent original WEB_INLINE IR009 must review
the entire tree, not only delta, and count unresolved advisories.
Only 0 findings AND 0 advisories permits recommending Product acceptance;
never automatically accept, merge, deploy, close or change SOT.
No production database, Redis, credentials, schema migration or
new dependencies were accessed or modified.

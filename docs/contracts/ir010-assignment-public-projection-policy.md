---
document_id: FF-IR010-POLICY-REPAIR-20261103-001
status: review_required
source: https://github.com/mauedgar/FitFlow/pull/61#issuecomment-6593544747
authority: user_approved_A16_A17_policies_and_extended_development
product_acceptance: false
merge_authorized: false
---

# IR010 successor — teacher assignment scope and public/API separation

## Frozen baseline and authorized Product policy

PR61 `aa6d9c30095b220c3a09507de141acdb827cf106`
tree `751e904b391facef5e6c8be72e3c8d12fa8b02dd` had
independent IR010 **0 findings / 7 advisories / NO_RECOMMEND**.

The user explicitly approved two Product policies after that review:
1. **A16** teacher sees only bookings on *assigned schedules* of their
   teacher profile. Admin and front desk retain role-wide operational
   visibility; clients remain limited to personal bookings.
2. **A17** public catalogues use dedicated safe public projection APIs,
   while broad operational list and detail APIs require authentication,
   with client frontend migration to public endpoints.

Approval of these two policies is not approval of a candidate, integration,
deployment, dangerous SQL, secret use or closure of the other advisories.

## A16 — authorization at the query boundary

- Teacher's JWT/DB account UUID maps to `Teacher.user_id`, not
  `Teacher.id`; joins to the schedule's `teacher_id` profile.
- Session and schedule booking detail endpoints deny a teacher with no
  assigned schedule (HTTP403), including UUIDs of another teacher.
- GymClass, day and range booking enumerations apply teacher assignment
  **within the SQL SELECT before LIMIT/OFFSET**. This prevents the
  pagination and cross-class leakage that could occur with filtering a
  role-wide result in memory.
- Admin/front desk retain broad operational coverage, but client/anonymous
  still receive their previously enforced 403/401 on booking enumerations.
- New PG15 HTTP fixtures create *two teachers with different User/Person
  UUIDs and two schedules on the same GymClass* plus bookings on both;
  negative cross-teacher and positive staff checks cover all five
  enumeration shapes and cross-teacher direct-detail rejection.
- No migration, new dependency, real user data, production DB/Redis,
  or teacher booking-write permission was introduced.

## A17 — safe public projections and explicit operational gates

- `GET /gym-classes/` and `GET /class-schedules/` now require signed
  operational roles (GymClass admin/front desk; schedules admin/front desk
  or teacher scoped to their own schedule profile).
- `GET /class-schedules/{schedule_id}` is a signed operational detail;
  teacher accesses only assigned schedule profiles.
- Existing public `GET /gym-classes/public`,
  `GET /gym-classes/{class_id}/public`, `GET /class-schedules/public`
  and class-scoped public schedule projections preserve their safe
  schemas. Public session availability and client weekly agenda
  contracts are not modified by this policy.
- Frontend `getAllClasses()` now reads `/gym-classes/public`, adapts
  the safe category entries to the current card type with an empty
  schedule array, and continues to fetch details via existing separate
  public class/schedule APIs. The app does **not** blindly expect the
  old broad operational response when anonymously browsing classes.
- Real PG15 HTTP tests cover signed admin/front_desk positive reads,
  anonymous 401, client 403, teacher-only own-schedule reads and
  public safe projection without timestamps/soft-delete/schedules.
- No globally versioned API rename; path semantics for previously
  anonymous operational GETs intentionally narrow as approved. Further
  external clients will need migration according to this contract.

## Other advisories — disposition is still evidence-dependent

- **A10 MEDIUM** lost HTTP response can leave a registered refresh token
  never received by the client; signed TTL bounds token lifetime, but
  cannot prove client-side revocation of an unseen credential. A
  versioned server acknowledgment protocol is a separate Product
  behavior choice, not assumed implemented.
- **A11 MEDIUM** browser-mounted/deployed E2E remains **NOT_RUN**.
  Node VM tests, HTTP contracts and frontend builds are not Playwright
  evidence. Isolated browser setup/environment and any installation
  require separately qualified grant and available host; staging Issue37
  does not imply browser PASS.
- **A12 MEDIUM** staging configuration rejects TESTING=true, but
  reverse proxy trusted client-IP policy, distributed/shared-IP fairness
  and account-wide lockout need environment-specific verification.
- **A13 LOW** pre-jti legacy refresh raw Redis keys remain readable for
  signed backward compatibility. Deleting production keys or removing
  fallback before their real signed expiry is not authorized.
- **A18 LOW** positive synthetic admin mutations are covered; reverse
  Passlib skips, independent schema archive unpack and mounted browser
  E2E still need explicit artifact or environment evidence.

Use exact CI on a new frozen SHA/tree with PG15/Redis7 Python3.11/12/13,
Ruff, Pyright, Node22/Vite, bcrypt, schema and structure, then obtain an
independent WEB_INLINE IR011 receipt. Only **0 findings + 0 advisories**
may justify *recommending* acceptance; no automatic acceptance,
merge, issue close, Phase2 or deployment.

# FitFlow — historical core-domain migration data-safety candidate

Date: 2026-11-05
Responsibility: FitFlow Control / M4 staging, Issue #40.
Source: `develop@55772398c72f4c1a41862dccd79b04d38016dfcb`, tree `ee59ccea9c4b6682a8ba0c739308b51214a8619d`.
SOT: v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`.

## Observed defect and scope

Independent IR020-P found the legacy revision `f5453ed20cdc` drops
`teacher_class_association` and truncates eight Product tables with CASCADE.
The loss hazard predates PR #83; it is not caused by Python 3.15.2.

This isolated safety candidate changes exactly the historical migration and
adds a synthetic unit proof. It does **not** claim to migrate preserved records.
It must refuse to cross this revision on a populated database.

## Guard semantics

- Before any new enum, DROP or TRUNCATE, acquire PostgreSQL transactional
  ACCESS EXCLUSIVE locks on the direct destructive targets, then query the
  non-system relation catalog and lock/check every user table. Any retained
  user row, including in a possible indirect CASCADE table or a separate
  association table, fails closed. The guard is deliberately conservative.
- Hold locks until the Alembic transaction commits or aborts. The implementation
  uses a 3-second per-lock timeout and a 20-second overall preflight budget.
- SQL identifiers from the catalog are identifier-quoted. No data is read
  beyond EXISTS predicates; no retained records are modified by the guard.
- Readiness or CI on an **empty disposable** database is not evidence of
  safely upgrading an existing populated database. Already-migrated
  databases are unaffected because Alembic does not replay applied revisions.
- Failing the preflight is a valid, non-destructive blocking result. No
  override, `stamp head`, forced reset, volume deletion, or automatic
  downgrade is authorized.

## Acceptance requirements

1. Run Ruff, Pyright and deterministic unit tests on the candidate SHA.
2. On disposable PostgreSQL 15 only, prove that a fresh empty migration reaches
   Alembic head, a seeded pre-revision fixture fails before any DDL/data loss,
   and rollback of the failed transaction leaves data and revision unchanged.
3. Independent review of both direct and transitive CASCADE effects and schema
   access permissions, plus same-tree DocImpact. No PASS transfer.
4. Before a retained-data rollout, inspect actual revision and affected data
   read-only, secure backup/restore rehearsal and author a **separate**
   data-preserving upgrade strategy if crossing this revision is required.
5. Staging release still needs an operator-visible preflight before container
   start; this in-migration guard prevents destructive effects on *all* invocations
   but is not the full external deployment workflow gate.

No real DB/Redis, secrets, production migration, automatic merge, release,
TaskCycle, or Issue closure is included in this candidate.

## Workflow qualification repair — separate failure before migration

The original push [run 42079896815](https://github.com/mauedgar/FitFlow/actions/runs/42079896815)
failed during job setup: `Unable to resolve action astral-sh/setup-uv@v10`.
No migration or test ran in that execution. The legacy workflow also contained
an unrestricted `git-auto-commit` schema mutation. This candidate adopts the
**read-only schema validation workflow** from PR #83's exact source blob
`f7999c6b05ec9ca46385a5585434e6b1342e22cf`, adapting the interpreter
to `develop` Python 3.11.17 only (not changing Product Python baseline).
The workflow installs pinned uv, upgrades a disposable PG15 fixture, compares
two schema dumps and uploads an immutable artifact; it never writes to Git.

Previous run failures are preserved; the successor requires new exact CI.

## IR001 repair candidate, after exact run failures

IR001 on commit `94c96fc5207d6bb107a249e501931888108c7cfb`
reported F001/F002/F003 and A001/A002/A003; no historical PASS is
transferred. Native baseline [run 42080556397](https://github.com/mauedgar/FitFlow/actions/runs/42080556397)
failed collection: importing the migration file from pytest resolved the
local `backend/alembic` package rather than the installed package.
The new unit tests compile the *exact AST* of the guard and statically
check that it is the first upgrade effect, avoiding package shadowing.

Scope of repair:
- Enumerate PostgreSQL `pg_class` regular and partitioned relations
  across schemas rather than merely `pg_tables`. Reject foreign and
  materialized relations rather than silently claiming completeness.
  Refuse session temporary relations. All catalog identifiers are quoted.
  Lock target relations before catalog inspection and other relations before
  occupancy checks; fail on permissions or lock conflicts.
- One 20-second monotonic deadline is converted into remaining PostgreSQL
  `statement_timeout` for each statement; bounded lock waits (3 seconds).
  A failure aborts the Alembic transactional upgrade. It may reject unrelated
  populated tables intentionally; it never attempts to preserve data.
- Add a disposable PG15 **negative fixture** to `update-schema.yml`:
  reach predecessor `a2b62b427037`, seed isolated retained data, expect
  an exact `f5453ed20cdc` fail-closed error, assert both data and revision
  survive; keep the original positive empty-database migration.
  No real/staging/production DB, no reset or volume deletion.
- Residual operator gate: preflight before `docker compose up`, least-
  privileged role qualification, retained-data upgrade plan and backup/
  restoration are separate prerequisites. An already-applied revision does not
  run this historical guard again.

Fresh original CI and a new independent IR are required for this successor.

## IR002 follow-up — direct target, FK child, explicit schema and non-superuser

IR002 (subject `fe21a34a46e055a12ae86d9a8b8a0ddf2e245f0f`, tree `76346bbb4b9dcfcc0647804937577eedb7c2b546`) was PARTIAL,
not a global PASS. Baseline run 42081839293 and schema run 42081839356
subsequently finished SUCCESS on their **original** subject; they do not
qualify a successor commit.

This candidate closes the missing scope of the real disposable PG15 negative:
1. Seed a nonempty `gym_classes` legacy table immediately before
   `f5453ed20cdc`, attempt upgrade and verify explicit rejection and row+
   Alembic predecessor revision preservation.
2. Create a real FK-dependent child with a preserved row. Repeat upgrade,
   expect the same refusal and verify both parent and child survive.
3. Exercise a non-superuser database-owner migration account against a
   third disposable PG15 database (rather than assuming CI superuser
   equivalence). This qualifies owner permissions, **not** least-privilege
   non-owner deployment grants.
4. Reject `current_schema() != 'public'` before any DDL and lock every
   direct target using explicit `"public"."table"` names. PostgreSQL
   catalog scans continue to include other schemas; a user table with data
   in another schema also blocks. The requirement for a public-schema
   historical revision is fail-closed, not support for arbitrary search_path.

No retained real data, destructive rerun, deployment, or preflight override.
Operator-side preflight before `docker compose up`, backup/restore
qualification, and a forward-preserving migration strategy for populated
legacy DBs remain separate non-negotiable gates.

## Native CI fixture correction (new candidate)

Source `4dd2145da0ab580387a71cbe6325dc3967f71f9b` schema run 42083677800 terminated FAILURE **before** reaching
negative migration invocation: the pre-refactor column `gym_classes.default_capacity`
is NOT NULL (historical revision `6beb1fc321fd`). Inserted fixture omitted
this column and was rejected by PostgreSQL with NotNullViolation. The
successfully verified fixture schema now supplies `default_capacity=8`
while preserving the same synthetic gym_classes UUID and FK-dependent child
checks. The failure is evidence of an invalid fixture, not a destructive
migration or observed retained-data loss. Fresh original CI and independent
review are required on the successor SHA. Earlier 42081839293/42081839356
PASS and 42083677800 FAILURE remain tied only to their own commits.

## IR005 independent review follow-up — RLS and timeout isolation

IR005 independently verified subject `67ba909fab3e81b3c0c87d49efef19ec624c322d`
and original schema/baseline success (42084915363 / 42084915404);
verdict **NO_RECOMMEND** (F001 RLS-hidden rows, A001 transaction-local timeout
restoration, A002 separate operator retained-data deployment qualification).
This new candidate must not inherit that CI or review result.

- F001: after acquiring each table lock, re-read `pg_class.relrowsecurity`
  and `relforcerowsecurity` using bound identifiers; refuse enabled/forced
  row security before `SELECT EXISTS`, even if the current migrator can
  bypass policies. Disallow rather than bypass or assume complete visibility.
- F001 proof: disposable PostgreSQL 15 database owned by a non-superuser,
  populated legacy `gym_classes`, `ENABLE` + `FORCE ROW LEVEL SECURITY`,
  deny-all SELECT policy, and exact preservation of the row and predecessor
  Alembic revision after the rejected upgrade. The unit stub covers the
  fail-closed path; a new original CI run is needed for empirical proof.
- A001: capture and restore both `statement_timeout` and `lock_timeout`
  within the existing Alembic transaction after a successful preflight.
  Any failure still aborts the whole transaction with no manual override.
- A002 remains a distinct unqualified external gate: operator-visible
  preflight, least-privilege migration account, backup/restore rehearsal and
  a preserving migration for existing data. This guard is **not** a safe
  populated-database upgrade or authorization to launch staging.

This repair is scoped to PR #89, unchanged Product API and original
historical migration revision ID; no `develop` integration or beta launch.

## Backend CI assertion correction (successor of c32e7e9)

Native baseline job `42094383673` was terminal **FAILURE** on
`c32e7e9236b4ddc6fcf6b9bc60c36048da00fbfe`: 266 passed and one
unit assertion failed because the existing ACCESS EXCLUSIVE SQL index was
not updated after insertion of two `current_setting` calls.
`conn.sql[3]` is `SET LOCAL lock_timeout`; the target lock is now
`conn.sql[5]`. The minimal repair changes only that assertion index.
The independent PG15 schema workflow `42094383676` was SUCCESS on the
original failing baseline SHA. Neither CI verdict transfers to this
successor; fresh exact runs and independent review remain required.

## IR006 PASS_SEGMENT follow-up — timeout evidence

IR006 independently verified `4e2c77b055b0e91f22003a2dede8a8fd865159ea`
with exact CI runs `42095241281` (schema PASS) and `42095241129`
(backend/frontend PASS, 267 tests). It issued PASS_SEGMENT, 0 findings
and 2 advisories: A001 requested explicit coverage for pre-existing
non-default PostgreSQL statement/lock timeouts; A002 remains the
separate external retained-data deployment gate.

This successor adds parametrized unit coverage of **two distinct
non-default timeout pairs** and asserts restoration preserves each
original value. Production migration SQL and its refusal semantics
remain unchanged. The separate A002 external operator preflight,
backup/restore and forward-preserving strategy remain unqualified.
A new exact CI and IR are required before recommending any acceptance.

## IR007 A001 repair — stateful timeout stub (new candidate)

IR007 reviewed `982bd63a7fcc160c39d761f49a428128a6502180`
with native schema run `42096307879` and baseline run `42096308473`
(both SUCCESS), returning `PASS_SEGMENT / 0F / 1A`. Advisory A001
(LOW) observed that the test stub only recorded `set_config` calls
without modeling their effect on effective timeout settings.

This successor changes **only the isolated test stub and DocImpact**.
The stub tracks transaction-local `statement_timeout` changes and
`SET LOCAL lock_timeout`, then tracks their restoration. Parametrized
non-default timeout tests assert both an intermediate change and
exact final value restoration. The production migration and schema
workflow are not modified.

R007 remains `NOT_READY`. Deployment prerequisites (operator
preflight, backup/restore, least-privilege runtime and a data-preserving
upgrade for populated databases) remain separate and unresolved.
Fresh original CI and independent IR are necessary for this successor;
prior CI/IR verdicts do not transfer.

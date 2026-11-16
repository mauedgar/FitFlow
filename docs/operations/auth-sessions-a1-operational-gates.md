---
document_id: FF-OPS-AUTH-SESSIONS-A1-001
status: review_required
responsibility: FITFLOW-C013-G2A1
product_scope: proposed_operations_doc_only
proposed_target: docs/operations/auth-sessions-a1-operational-gates.md
---

# G2-A1 auth_sessions: disposable qualification and retained-data stop gate

> **PROPOSAL ONLY — not canonical FitFlow policy, not a deployment authorization.**
> This text is staged in GitHub Transport for a separately reviewed Product DocImpact.
> Its Product target remains absent until independent review and Developer promotion.

## Subject and evidence

The inert A1 persistence candidate is [FitFlow PR #109](https://github.com/mauedgar/FitFlow/pull/109), frozen at
[commit `7db818fca0178f7c2edee1a43c0d5d164e9c8d2b`](https://github.com/mauedgar/FitFlow/commit/7db818fca0178f7c2edee1a43c0d5d164e9c8d2b),
tree `ae0de5f99c2364cc724de66114a7d8c807950eab`,
stacked on [PR #107](https://github.com/mauedgar/FitFlow/pull/107)
HEAD `50950642e7da8280deecd67a6b039751c329bc1d`, with
`develop@c8bedd52cc3663f773dbe623f381c83392893dce` as the
frozen original baseline. **At this observed baseline**, Product SOT
v5.3 and AGENTS v5.2 govern. Reobserve both before promoting this
proposal: PR #110 may change AGENTS if separately accepted.
No Product integration or migration to retained DB is established.

### Native CI evidence and attribution

The independent [IR007 ORIGINAL](https://github.com/mauedgar/ts-execution-transport/blob/66a927fcf6a1d0a8f516f78e9c2260ac06d52bc8/results/FITFLOW-C013-PR109-G2A1-OPERATIONS-IR007-20261115-001/ORIGINAL.md)
confirmed four commit-associated workflows with `completed/success`,
but explicitly marked each run's exact `head_sha`, `run_attempt`,
and raw backend pytest count as **NOT_VERIFIED_IN_IR007**.
These fields were **separately verified by FitFlow Control 013 from
native GitHub Actions REST records and raw backend job logs**, not
by IR007. Control observed `head_sha` equal to the frozen commit,
`run_attempt=1`, `status=completed`, `conclusion=success` for:

- [Schema run 43708380735](https://github.com/mauedgar/FitFlow/actions/runs/43708380735)
- [Deterministic run 43708412244](https://github.com/mauedgar/FitFlow/actions/runs/43708412244)
- [Baseline PG15/Redis7 Python 3.15.2 run 43708412232](https://github.com/mauedgar/FitFlow/actions/runs/43708412232) — backend job `132794515212`, native log: **451 passed, 1 warning in 48.00s**
- [Signed ADMIN disposable E2E run 43708412192](https://github.com/mauedgar/FitFlow/actions/runs/43708412192)

This distinction preserves IR007's original evidence limits; the
separate Control receipts do not rewrite its independent verdict.
IR007 remains `OPERATIONS_RULING_RECOMMEND`, **0 new A1 findings /
2 operational advisories**, not Product `0F/0A`, a merge grant or
qualification for retained data. See the frozen
[R5 persistence contract](https://github.com/mauedgar/ts-execution-transport/blob/c31f8a15bd77306ce25337669550b79f98411fdf/plans/FITFLOW-C012-ISSUE108-G2-A1-SCHEMA-R5-20261113-001/SCHEMA_R5.md)
and [operational ruling](https://github.com/mauedgar/ts-execution-transport/blob/774071bf5aa7023620035af0931d28e0713fd80e/plans/FITFLOW-C013-G2A1-OPERATIONS-GATE-20261115-001/OPERATIONS_RULING.md).

## Disposable test qualification — only within the defined runner

The qualified backend workflow is
`.github/workflows/fitflow-baseline-ci.yml` on `ubuntu-24.04`
**GitHub-hosted** Actions with new disposable VM per job, pinned
PostgreSQL 15-alpine and Redis 7-alpine service containers, loopback
`127.0.0.1:5432`, database `fitflow_test`, dedicated synthetic
principal, checkout SHA/tree checks, Python 3.15.2 and Alembic upgrade
before test execution. The fixture's unique `fitflow_a1_probe_<uuid>`
database is permitted to be created/dropped by the *disposable CI-only*
PostgreSQL test admin.

The `GITHUB_ACTIONS` environment variable, database name, loopback
address and `finally: DROP DATABASE` are preflight controls, **not**
authentication or proof of data destruction. The GitHub-hosted ephemeral
VM teardown is the enclosing disposal boundary. A job interruption or
DROP failure is an execution anomaly to record; it must never be
reinterpreted as confirmed per-database cleanup. The tests **MUST NOT**
be run against retained local databases, self-hosted Actions runners,
external PostgreSQL or a production/staging instance without a fresh
Developer gate and new isolation qualification.

A change to runner class, workflow version, containers, credentials,
network boundary or volume persistence invalidates this qualification.

## Retained database: entry is BLOCKED until separately approved

**The following are future preconditions, not controls already
implemented or authorized.** No retained database has been qualified
by this proposal. Before any migration, cleanup or removal involving
retained data, a separately authorized Developer operation must define,
implement, independently validate and record all of the following:

1. **Release/restore:** precise commit/tree and forward-only Alembic
   revision, full database backup, independently tested restore, old
   application compatibility or forward-fix plan; no destructive
   Alembic downgrade or volume deletion.
2. **Roles:** distinct minimal privileges for migration owner, runtime
   application and cleanup actor, enforced through SQL GRANT/REVOKE
   on an isolated representative environment. The runtime identity
   must never own session tables, disable triggers or acquire
   CREATEDB/SUPERUSER/BYPASSRLS to evade invariants.
3. **Session retention:** before removing any session, verify
   `logout_proof_expires_at <= clock_timestamp()` using authoritative
   PostgreSQL time and appropriate row locks. The actual BEFORE DELETE
   trigger remains enforced. An absent row is not a logout receipt.
4. **Account erasure:** ordinary User `deleted_at` soft deletion does
   not revoke tokens. User hard deletion requires separately authorized
   policy and proof all child session rows became eligible and were
   legitimately deleted; FK `ON DELETE RESTRICT` must not be bypassed.
   Conflicting privacy/legal retention requirements require a separate
   audited ruling, not informal superuser manipulation.
5. **Measured resource budget:** use disposable multi-user/selectivity-
   skew data, not only the 4,096-row synthetic index test. Record
   representative `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`, lock and
   statement timeouts, maximum rows per transaction, elapsed/IO and
   p95/p99 resource consumption, rate limits, and stop thresholds.
   Numerical limits are **NOT SET** until those measurements and
   a separate Developer decision.
6. **Least-privilege cleanup/audit:** separate authenticated cleanup
   actor, bounded idempotent batches, dry-run, explicit audit of
   actor, operation, row counts, failed SQLSTATE, schema/release,
   restore receipt and sampled DB clock. Redact user PII and all
   secret or proof material. Unexpected rows, lock waits, unknown
   commit, missing key/permission or failed cleanup => STOP/UNKNOWN.
7. **Key retention:** A2/Ops must preserve JWT signing-key identifiers
   and versioned receipt MAC verification material until the maximum
   dependent `logout_proof_expires_at` and permitted grace have
   elapsed; handle missing/compromised keys as UNKNOWN/PENDING, never
   fabricated 204 logout confirmation. The A1 table itself does not
   sign tokens or implement logout HTTP semantics.

Until those prerequisites and a new Developer gate PASS, remain in
`BLOCKED_PRECONDITION`. No scheduled cleanup job is installed by
A1. Synthetic EXPLAIN, SQLSTATE 23514/23503 negative tests and
FK/trigger evidence do not constitute retained-data cleanup authorization.

## Phase boundaries and external dependencies

G2-A1 is only an additive, initially empty table, ORM/CRUD/service
staging contract and tests. Auth guards, registration, refresh
rotation on real traffic, signed logout proof, COMMIT-before-JWT/204,
fail-closed database guard behavior and lost ACK recovery belong to
separately authorized G2-A2. HttpOnly cookie, CSRF/Origin and frontend
token transport belong to Phase B. No Product release or beta
readiness is inferred from A1.

PR #107 is the stacked predecessor and remained unmerged at the
frozen observation. Separate Extraordinary Control [PR #111](https://github.com/mauedgar/FitFlow/pull/111)
contains overlapping test-only proof based on an older PR #109 HEAD;
do not cherry-pick, rebase, merge or close it without its owner's
reconciliation. Separate docs [PR #110](https://github.com/mauedgar/FitFlow/pull/110)
owns its delivery-process policy and an independently reported ruleset
mismatch; its proposed AGENTS v5.3 is **not** the currently accepted
AGENTS v5.2 at this frozen baseline. Reobserve Product refs, policy
and ownership before creating or merging any Product docs-only PR.
Never forge a required check or bypass branch protection.

If Product source/runner/ruleset changes, reobserve identities,
the SOT and relevant operational receipts. An independent reviewer
verdict remains advisory evidence, not acceptance or permission
to integrate or run an operation.

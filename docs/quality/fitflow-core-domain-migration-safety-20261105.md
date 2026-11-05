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
- Hold locks until the Alembic transaction commits or aborts. Fixed 5-second
  lock timeout fails closed rather than waiting indefinitely for contention.
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

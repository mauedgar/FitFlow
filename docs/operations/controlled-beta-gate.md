---
document_id: FF-OPS-CONTROLLED-BETA-GATE-001
status: accepted_pending_implementation
machine_context: true
milestone: M4_STAGING_AND_BETA_READINESS
responsibility: R007
---

# Controlled beta decision gate

## Authority

This gate answers only whether FitFlow has sufficient technical evidence for a
Developer beta decision:

- `READY_FOR_BETA_DECISION`; or
- `NOT_READY_FOR_BETA_DECISION`.

It cannot return or authorize `LAUNCH_BETA`. Hosting selection, provisioning,
public DNS/TLS, participant policy, support ownership, and launch remain separate
Developer decisions. The executable policy surface is
`docs/operations/controlled-beta-gate.yaml`.

## Entry evaluation

Evaluate every `entry_conditions` item in the YAML against exact candidate
evidence. Missing, stale, mismatched, or unverifiable evidence is a failure, not
an operator judgment call. Evidence must identify the candidate commit and tree,
configuration digest, command, scope, and output.

The gate binds to demonstrated M4 responsibilities:

- R002: explicit fail-closed staging inputs and secret boundary;
- R003: isolated PostgreSQL/Redis topology, migration-first backend, pinned
  frontend build/runtime, Nginx serving, and API proxy;
- R004: liveness, PostgreSQL/Redis readiness, configured logging level, and
  visible startup/access/error logs;
- R005: revision-tagged deploy/redeploy and conservative application rollback;
- R006: repeatable synthetic MVP vertical through real HTTP interfaces.

`READY_FOR_BETA_DECISION` requires all technical conditions to pass. It may
coexist with the explicitly listed external decisions because its purpose is to
present a bounded technical candidate to the Developer, not resolve those
decisions.

## Operator check

Before presenting the gate result:

1. Confirm the exact commit, tree, image revision labels, and clean worktree.
2. Confirm `deployment-state.json` matches the revision and approved
   configuration digest.
3. Confirm PostgreSQL, Redis, backend, and frontend are healthy.
4. Confirm `/health/live` is `alive` and `/health/ready` is `ready`.
5. Confirm the database is at the candidate Alembic head.
6. Inspect backend startup, access, warning, and error logs.
7. Run the R006 smoke twice from fixture reset and retain both outputs.
8. Confirm deploy, redeploy, and exact-schema application rollback rehearsals.
9. Record known-limitations acceptance and all remaining Developer decisions.

Do not mark the gate ready when a command was skipped, evidence belongs to a
different revision, or health was inferred from container process state alone.

## Observation and incident response

The available observation boundary is intentionally basic: Compose health and
restart state, process liveness, PostgreSQL/Redis readiness, migration startup,
Uvicorn access/error logs, and Product HTTP outcomes. Metrics, alert routing,
and tracing are not present and cannot be implied.

When an incident condition in the YAML occurs:

1. Stop admission of new beta activity; this does not delete data.
2. Capture revision, configuration digest, service health, readiness response,
   and bounded logs with secrets redacted.
3. Attempt at most one same-revision redeploy when state and schema identity are
   intact.
4. If the critical vertical still fails, evaluate R005 application rollback.
5. Roll back only when exact Alembic-head equality and explicit compatibility
   confirmation pass.
6. Otherwise stop and return to CONTROL for a forward-fix or reviewed recovery.

No step authorizes an Alembic downgrade, volume deletion, hidden data repair, or
external infrastructure change.

## Data and support boundary

The R006 fixture reset owns only its reserved synthetic IDs. It is not a beta
data reset mechanism. Retained beta data has no autonomous reset policy; backup,
restore, retention, and destructive recovery require explicit Developer policy
before launch authorization.

Repository tooling supplies technical checks and stop/rollback procedures. It
does not choose the operator, support channel, response window, or escalation
owner. Those values must be recorded before any separately authorized beta.

## Decision record

The gate record must contain:

```yaml
result: READY_FOR_BETA_DECISION | NOT_READY_FOR_BETA_DECISION
candidate_commit: <full-sha>
candidate_tree: <full-sha>
technical_conditions:
  R002: PASS | FAIL
  R003: PASS | FAIL
  R004: PASS | FAIL
  R005: PASS | FAIL
  R006: PASS | FAIL
active_stop_conditions: []
accepted_known_limitations: []
external_decisions_remaining: []
launch_authorized: false
```

An empty `accepted_known_limitations` list does not silently accept limitations;
it means acceptance remains unresolved. `launch_authorized` is always `false`
for this gate.

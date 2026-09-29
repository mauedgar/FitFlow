---
task_id: TASKCYCLE-FITFLOW-M4-WAVE-B-BETA-OPERATIONALIZATION-001
status: PENDING_ACCEPTANCE
task_type: tooling
area: mixed
scope: mixed
lane: ai_orchestrated
risk: medium
priority: P1
baseline_commit: eb7ed59c74b72a23ecc0f1d440dbb8afd51e80f1
baseline_tree: 2b49b09f89a1bff6d29f07de8d7484519abee1ce
wave: M4_WAVE_B_BETA_OPERATIONALIZATION
milestone: M4_STAGING_AND_BETA_READINESS
---

# FitFlow M4 Wave B beta operationalization

## Objective

Produce one provider-neutral operational contract spanning R005 deployment,
redeploy, and rollback; R006 deterministic MVP vertical smoke; and R007
controlled-beta decision gating. Preserve isolated responsibility checkpoints
and create one terminal Wave candidate and independent review input package only
if all three responsibilities pass.

## Required documents

- `docs/SOURCE_OF_TRUTH.md`
- `docs/program/milestones/M4-staging-beta-readiness.md`

## Ownership

- `config:docker-compose.staging`
- `path:scripts/staging`
- `doc:staging-operations`
- `path:.ai/tasks/TASKCYCLE-FITFLOW-M4-WAVE-B-BETA-OPERATIONALIZATION-001`

## In scope

- provider-neutral local staging-like deployment operations;
- deterministic non-production fixture bootstrap and real-interface smoke;
- beta admission, observation, incident, stop, and rollback decision gate;
- bounded validation, isolated commits, candidate identity, and review package.

## Out of scope

- hosting provider selection or provisioning;
- external staging deployment, DNS, TLS, or publication;
- destructive database rollback guarantees;
- beta launch, participant selection, pricing, or M5;
- integration into canonical `develop`.

## Acceptance criteria

- R005 passes with a rehearsed deploy/redeploy/rollback procedure and explicit
  non-destructive database boundary.
- R006 passes twice from deterministic isolated state through real HTTP and the
  frontend proxy.
- R007 yields READY_FOR_BETA_DECISION or NOT_READY_FOR_BETA_DECISION without
  authorizing LAUNCH_BETA.
- Complete-candidate regression and staging-like health validation pass.
- The independent review ZIP is byte-faithful and reconstructs in an empty Git
  repository with no external object prerequisites.

## Authority boundary

Internal commits and the terminal candidate are authorized. Integration,
publication, external deployment, beta launch, and M5 selection are forbidden.
Only the developer may promote this TaskCycle from PENDING_ACCEPTANCE to DONE.

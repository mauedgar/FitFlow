---
document_id: FF-OPS-EXTRAORDINARY-DELIVERY-20261114-001
status: candidate_pending_product_integration
owner: FitFlow Product Control (extraordinary, delegated by Developer)
effective_scope: FitFlow only
date: 2026-11-14
baseline: develop@c8bedd52cc3663f773dbe623f381c83392893dce
---

# FitFlow — Risk-adaptive delivery / Product-first v1

## Developer ruling and authority boundary

On 2026-11-14 the Developer approved replacing five uniform process restrictions
with proportional, evidence-backed delivery rules and authorized canonical
repository proposals and the bounded work described below. This is a **new**
Product process policy candidate, not retroactive approval of any prior
Independent Review, TaskCycle, ExecutionAttempt, candidate, merge, or beta.

FitFlow Control 013 is paused. **FitFlow Control Extraordinario** may establish
the delivery policy, reconcile exact existing attempts, prepare independent
implementation and validation work, and submit integration proposals. It must
not write concurrently to Control 013's frozen PR #107/#109 worksets, start
duplicate reviews, or convert a stale/frozen receipt to PASS. On resumption
Control 013 observes its own provider-native result before choosing a new effect.

Canonical Product code and independently verified behavior outrank this document.
`docs/SOURCE_OF_TRUTH.md`, accepted Product contracts and the M4 controlled
beta decision gate remain in force. This policy modifies only *future*
procedural routing after its separate competent acceptance; never creates an
authorization for production deployment or retained-data mutation.

## Five approved reforms

1. **Risk-weighted acceptance instead of universal 0F/0A.**
   Use the matrix below. An unresolved advisory is a documented disposition,
   not silently closed. Serious security/data-integrity findings remain blocking.
2. **One final independent semantic review per stable candidate**, after
   bounded incremental deterministic CI. Request an extra focused IR only for
   material high-risk changes, new findings, or review-input changes. Preserve
   immutable historical reviews; never repeat an identical attempt.
3. **Delegate routine decisions within an explicit Developer grant.**
   Low-risk documentation, test fixtures and isolated non-security code may be
   committed/pushed/merged only where a grant identifies repo, branch,
   write-set, tests, invariants and allowed effect. A CI PASS or IR PASS alone
   never grants Product acceptance. If a grant does not cover merge, stop.
4. **Prefer small, independent and promptly integrable PRs.**
   One functional objective per candidate and one owner per overlapping path,
   API contract or migration. Use small merges without unnecessary
   cross-repository gates; when security changes demand serial composition,
   preserve them as exceptional work rather than expanding every PR.
5. **Infrastructure is a dependency only when the actual vertical needs it.**
   Prefer native GitHub and already qualified CI/staging scripts. Do not require
   unrelated TS Remote State, Tecnotron post-init, Codex Cloud adoption,
   OpenCode2 qualification or extra provider experiments for ordinary FitFlow
   development.

## Risk tiers / acceptance policy

| Risk | Examples | CI and review | Disposition |
| --- | --- | --- | --- |
| LOW | docs, isolated fixtures, test-only, harmless UI text | Bounded deterministic checks; targeted peer/readback review when needed | May accept with recorded nonblocking LOW advisories after delegated grant |
| MEDIUM | new public read-only UX/API, internal service behavior without auth/data lifecycle changes | Exact SHA CI, E2E relevant to change, one independent final IR | 0 demonstrated blocking findings; LOW/MEDIUM advisories must have owner, reason, expiry/next gate and release impact |
| HIGH | JWT, logout, roles, session revocation, auth cookies/CSRF, DDL, retained records, capacity/concurrency or security boundaries | Exact SHA full relevant CI/negative E2E and independent security/semantic IR | No unresolved HIGH/CRITICAL findings or unsafe residuals; no known material integrity/security advisory waived merely for schedule. New Developer ruling for exceptions |
| RELEASE | public exposure, real secrets/hosts/retained DB, beta/prod data | M4 R007 entry conditions and separate operational review | Explicit Developer decision; readiness is not launch |

"0 demonstrated findings" is a **scope-bounded** statement, not certification
that no defects exist. An advisory may be deferred only with `id, severity,
evidence, impact, owner, mitigation, deadline/trigger, validation`; unresolved
severe risk remains a STOP. Do not re-label a finding as an advisory to meet
a metric, and do not downgrade prior reviewer verdicts.

## Operating / reviewer routing

- ChatGPT Web: sole FitFlow Product Control and Developer-ruling coordinator.
- OpenCode2: preferred **local** bounded implementer in a visible Orca-owned
  Windows/WSL terminal; never launch bare via Commander by default. Its ability
  and exact host/session must be verified before dispatch.
- Codex Cloud: **optional experimental** second implementer only for distinct
  path ownership/fixture or staging tasks; its adoption and execution receipt
  require qualification. It is not an automatic fallback or canonical reviewer.
- Review: independently selected per candidate (WEB_INLINE, OpenCode2, or
  another competent distinct provider). No paid LLM/API quota assumption;
  no implementer self-approval. Full frozen input and original receipt where
  required by the relevant already-adopted review contract.
- GitHub: native PR, immutable SHA/tree, CI and durable evidence. Serial merge
  after current target and ruleset re-observation; non-forced only.
- Commander: only previously determined bounded mechanical transport/execution;
  no repository exploration or semantic patch construction.

Two active implementers by default, max three if ownership and runtime are
actually independent. Exclude shared auth routes, lockfiles and migrations from
parallel write sets. STOP on unknown original effects, conflicts or missing grant.

## Control 013 handoff — original state frozen

Observed Product target: `develop@c8bedd52cc3663f773dbe623f381c83392893dce`
(tree `c4604a91fb899245071b8b14d55fab6893bdf0fa`).
- PR #107: OPEN, not merged/accepted, HEAD
  `50950642e7da8280deecd67a6b039751c329bc1d`.
  Its 5 native CI checks were reported SUCCESS; logout limitations rejected.
- PR #109 G2-A1: OPEN/DRAFT, stacked on PR #107, HEAD
  `f925dc70b3f8fee84154dcc554415bf9b89f5238`,
  tree `54637638ad7d6a50134f6780ca188db18efd3334`.
  4 exact original CI SUCCESS; 449 backend tests pass/1 warning.
- Original independent IR005
  `FITFLOW-C013-PR109-G2A1-FULL-IR005-A001` is terminal:
  `CONDITIONAL_RECOMMEND_A1_ONLY`, 0 demonstrated new A1 Product findings,
  **4 OPEN advisories**, not a global 0F/0A, not acceptance. ORIGINAL preserved
  at `ts-execution-transport@4761191b7b7ae9dc7db81aa7b2700f8d1119aee8`
  `results/FITFLOW-C013-PR109-G2A1-FULL-IR005-20261114-001/ORIGINAL.md`.
  No duplicate IR dispatch.
- IR005 A01/A02: disposable CI/test privilege boundaries; no retained SQL.
  A03: HIGH if A1 is mistaken for committed logout/token semantics; A2 remains
  distinct mandatory security work. A04: INDEX/EXPLAIN and erasure/retention
  policy before retained DB, with HMAC/keys remaining in A2.
- Do not close Issue #108, merge PR #107/#109 or deploy solely under this
  handoff. A1 read-only operational-proof work must be disjoint from A2.

## Five-step execution and functional DoD

**G0 Reconcile (now):** observe current branch heads, open PRs, IR005 original,
run receipts, active owners and ruleset. No reruns or rewriting frozen subjects.

**G1 Separate candidates:** identify minimal integrable changes from PR107,
preserve original auth candidate, classify any safe subset. For PR109 A1 prepare
only the already-pending operational INDEX/EXPLAIN, retention and erasure policy
gate on a fully disposable PostgreSQL database; no retained data.

**G2 Resolve auth separately:** full credential/commit-before-204/refresh-purpose
JWT/logout revocation E2E, Redis failure/ACK_UNKNOWN, legacy compatibility,
cookies/CSRF as separately authorized security work. Developer rejected prior
logout residuals; do not mark them safe by changing review policy.

**G3 Parallel staging:** reuse `docker-compose.staging.yml`,
`scripts/staging/release.ps1`, `scripts/staging/smoke.ps1` and native M4
R002–R006. Disjoint runner/fixture ownership; one repeatable disposable
PostgreSQL+Redis+backend+frontend test, no public infrastructure, no historical
DB/schema reset. Exact candidate binding before declaring new PASS.

**G4 Functional E2E / decision:** demonstrate client registration producing
Person/Client, signed login, schedule lookup, booking/capacity, ADMIN access and
logout/revocation across reload and failure modes; both negative permission tests
and expected successful HTTP. Capture exact SHA, commands, CI and data fixtures.
Evaluate `READY_FOR_BETA_DECISION` vs `NOT_READY_FOR_BETA_DECISION` only
under `docs/operations/controlled-beta-gate.yaml`. Never infer `LAUNCH_BETA`.

## Velocity feedback / experiment

Timebox the *measurement experiment* to five working days, not a promise of beta:
record PR lead time, integration throughput, blocker types, avoidable IR loops,
E2E feature completions and Developer interventions. Start with an existing
candidate; prioritize usable verticals over extra harness construction.
When a risk control demonstrably prevents the functional vertical, document
the exact cause; otherwise move it off the Product critical path.

## Stop / no implicit effects

This document alone does not authorize a merge, new Product TaskCycle,
OpenCode2/Codex dispatch, secrets, retained SQL, ruleset administration or beta.
Existing frozen grants remain exact. A broad preference for autonomy does not
supply missing native execution receipts. UNKNOWN remains fail-closed.

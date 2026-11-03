---
document_id: FF-ISSUE36-CI-CADENCE-DOCIMPACT-20261103-001
status: candidate
issue: 36
baseline_develop: c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d
baseline_tree: 9a2033e862535d6c0dc72b97a284811b1f401175
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# Issue #36 — Reduce unnecessary workflow activity without losing coverage

The existing [FitFlow Control cadence](https://github.com/mauedgar/FitFlow/issues/36#issuecomment-6607251180)
uses local targeted validation during implementation, one broad exact-SHA
CI set for a frozen candidate, one original separate-context IR per candidate,
and post-merge verification for the one accepted cumulative integration.
It does **not** authorize a new Product lifecycle or acceptance bypass.
`docs/quality-and-validation.md` v5.0 and the Product SOT remain authoritative.

## Immediate bounded code change

The legacy `.github/workflows/auto-pr-description.yml` uses the
`synchronize` event and rewrites the entire human-authored PR description
with every commit message. In long-lived cumulative PRs it causes an
unbounded, misleading summary, concealing original scope and DocImpact.

This candidate changes only that presentation workflow:
- respond to PR `opened` once, not `synchronize`;
- fetch current GitHub PR body and **leave any authored description intact**;
- only initialize an actually empty body with a bounded last-eight-message
  summary; re-fetch before writing to reduce concurrent edit clobbering;
- retain existing `GITHUB_TOKEN` permission, no extra secrets, no LLM,
  no changes to Product, backend/frontend, authentication, tests or migrations.

## Remaining Issue #36 work (not falsely declared implemented)

The six costly CI workflows on stacked PR68 remain exactly as authored
until reconciled with the accepted Product candidate. Github PR path
filters operate on the cumulative base-to-head diff: even changing one
backend test on PR68 can retrigger broad backend Python3.11/12/13,
bcrypt compatibility, browser, topology, migration schema and metadata.
The bot fix is an independent small step, not a claim that this redundancy
has already been removed.

A later bounded isolated workflow refactor must distinguish fast
developer feedback vs broad exact-SHA qualification, preserve unique
negative scenarios, required checks, receipt identity and independent
review, remove duplicate full backend/frontend/quality jobs, and
retain SHA-pinned deterministic dispatch. Do not skip a required test
and relabel it PASS; do not remove code coverage to optimize latency.

## Validation and review

Before accepting this candidate, verify YAML parse and
`pull_request.types=[opened]`; negative cases with authored, blank
and concurrently edited body; no `synchronize`, no hidden paid
LLM or new secret; one original independent review at the frozen
commit/tree and competent Developer acceptance before merge.
Only this separate PR is affected, and PR68's security write-set
remains untouched.

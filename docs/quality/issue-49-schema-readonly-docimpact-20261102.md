---
document_id: FF-ISSUE49-SCHEMA-READONLY-20261102-001
status: candidate_pending_ci_review
date: 2026-11-02
owner: FITFLOW_CONTROL
scope: issue_49_schema_workflow_only
acceptance: NOT_ACCEPTED
merge: NOT_AUTHORIZED
---

# Issue #49 — read-only CI schema evidence candidate

## Frozen authority and parent
- Canonical develop: `c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`, SOT v5.3 blob `f36307af0777fd3b493792ad42115fec56ac44b3`.
- PR #48 parent candidate `9e6a34e22161d6f6f2c5f5dc76bf30993d7493a0`, tree `dd3e81896eab9803606b8fa86b768afbde21b325`; this isolated branch is NOT accepted/merged and does not rewrite PR #48 or #47 original terminal run.
- Original update-schema.yml used a branch-wide push trigger and a git-auto-commit action without an explicit write grant. That behavior had no complete validation receipt.

## Bounded repair
- Replaces implicit push/auto-commit with read-only pull_request/dispatch validation; `permissions: contents: read` and `persist-credentials: false`.
- PostgreSQL 15 disposable fixture only, Python 3.11 environment, original pinned backend requirements and immutable setup-uv action.
- Runs Alembic head on the CI fixture; generates two independent schema-only pg_dump snapshots and checks byte-for-byte determinism.
- Uploads generated schema, SHA-256 and checked-out subject SHA/tree as an immutable run artifact. Output never enters the repository, and worktree remains clean; no tracked schema.sql is silently created.
- Uses SHA-pinned checkout, setup-python, setup-uv and upload-artifact. No changed migrations, DDL, auth, booking, CRUD, lock, passwords, real data, staging or secrets.
- No assertion that generated schema is equal to a canonical tracked schema: no root schema.sql existed at this candidate ref. Choosing to version a reviewed schema requires a separate Developer decision.

## Validation and acceptance
- CI trigger on a review PR plus exact run/job/subject SHA/tree, schema digest and migration evidence must be recorded.
- Independent WEB_INLINE review needs to examine CI authority, schema artifacts and repeatability; no acceptance until 0 findings and 0 advisories on the eventual integrated final subject.
- Issue #43 legacy bcrypt/Passlib compatibility is a separate authentication-sensitive owner. No auth change is included.
- Keep PR #48 draft, #47/#49 open, SOT/develop untouched. No auto-merge or closure.

## Exact run observation and bounded fixture correction

- [Actions 41470064089](https://github.com/mauedgar/FitFlow/actions/runs/41470064089), job `125360974771`, subject `9b14bafeeacb17a299d57d8b239babc6e29ac786`: FAILED at Alembic fixture initialization because Pydantic Settings requires `SECRET_KEY`; no schema generated or auto-commit. This failure is not a migration graph regression.
- Added synthetic test-only `SECRET_KEY` scoped only to the disposable migration step; does not use or replace any Product/staging token.
- Replaced checkout/setup-python/upload-artifact Node 20 actions with SHA-pinned official Node 24 releases to avoid inherited runtime deprecation; refs resolved from official GitHub tag refs before changing them.
- The new commit requires its own exact run and independent review. No CI PASS or acceptance is inferred.

## Second exact-run observation

- [Actions 41470382275](https://github.com/mauedgar/FitFlow/actions/runs/41470382275), job `125362075625`, subject `7af147d07c96e7299f36f6cadebdcc197d1e4cd7`: checkout and Node24 action setup PASS, dependencies PASS, **all disposable Alembic PG15 migrations to head PASS**; schema determinism step FAILED.
- The hosted runner exposed `pg_dump 18.6` against PG15; back-to-back SQL files differed at byte 46 / line 5. This is tooling-version nondeterminism, not proved schema semantic drift. No output artifact was published by the failed run, and no auto-commit occurred.
- Bounded correction: invoke the same `postgres:15-alpine` image as a PG15 read-only client through Docker host network for both pg_dump passes. Keep strict byte comparison and fail closed on mismatch; no masking, sed filtering or commit. The next candidate SHA needs new CI.

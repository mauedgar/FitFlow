---
document_id: FF-ISSUE43-44-PY315-COMPOSITION-20261107-001
status: review_required
candidate_base: c8bedd52cc3663f773dbe623f381c83392893dce
candidate_base_tree: c4604a91fb899245071b8b14d55fab6893bdf0fa
source_of_truth_blob: f36307af0777fd3b493792ad42115fec56ac44b3
agents_blob: cada7147371d6cf5ddf4d99b452e44ba13b753ca
issues: [43, 44]
review_gate: NOT_RUN
acceptance: false
integration: false
---

# FitFlow — Candidate composition for native bcrypt and CPython 3.15.2

## Product ownership and intent

This is an isolated **candidate**, not an accepted migration. Its direct parent is the current canonical `develop` after the successful one-file PR #106 ADMIN E2E merge. Product rules and previously accepted security contracts remain authoritative. The scope is the pending Issue #43 migration from Passlib to native bcrypt, plus the Issue #44 dependency/runtime normalization to **CPython 3.15.2 as principal runtime**.

## Byte-grounded composition

- Start from `develop@c8bedd52cc3663f773dbe623f381c83392893dce` (tree `c4604a91fb899245071b8b14d55fab6893bdf0fa`). Do **not** use the old PR #83 branch as a parent.
- Reuse exactly the 17 remaining modified auth, signup, API, test, contract, workflow/dependency files from PR #105 `622323951da75d19a56aa517d044e3f6eaa316af` **except** replacement dependency and Python workflow blobs described below. The already merged E2E test `frontend/tests/adminSignedE2E.cjs` stays at the current `develop` blob `436ffa524c0c8ae4a663962c53606fae0325aab1`.
- Reuse `.python-version`, `pyproject.toml`, `uv.lock`, both generated requirements exports, and runtime/test Dockerfile blobs from PR #83 `660d7253c7eb619ff2bdf1ba16d620052efcf95c` *only where their byte identities match earlier uv generation evidence*. `pyproject.toml` declares Python `>=3.15,<3.16`, bcrypt 4.3.0, and Pydantic >=2.14.2. Historical successful PR #83 runs **do not transfer** to this new composed SHA/tree.
- Workflow adaptations retain the current Product workflow semantics while pinning Python3.15.2 on CI baseline, schema migration validator, signed ADMIN browser E2E, and deterministic manual validator. The legacy bcrypt vector fixture may continue using Python3.11 **only as explicitly isolated compatibility evidence**; it is not a Product service runtime.
- Original PR #83 security/auth/routes/frontend files are **not copied**. Preserve accepted ADMIN-only /users/{id}/public, JWT privacy, transactional User+Person+Client registration, and real PostgreSQL duplicate-email/concurrency/rollback tests already on current develop.

## Validation and independent review gates

Run only qualified, disposable new native GitHub Actions on **this candidate's exact SHA/tree**. Require `uv lock --check` and `uv export --locked` equality with both checked-in requirements; install and `pip check` on Linux CPython3.15.2; full backend tests against disposable PostgreSQL15 and Redis7, real Alembic `upgrade head`, bcrypt 2a/2b/2y legacy vectors and 72-byte/NUL HTTP boundaries; JWT refresh/logout and privacy/ADMIN-only access; public/client signup duplicate/race/rollback; ADMIN keyboard signed browser and client E2E; frontend tests/lint/build; schema migration negative tests; Ruff/Pyright if applicable; reproducibility/packaging checks; Windows qualification and Docker disposable build before claiming platform-general readiness.

**CI ruleset migration remains a separate exact authorized gate:** current develop rule `26657593` expects the old named `Backend PostgreSQL/Redis (Python 3.11)`. The proposed Product job has the truthful name `Backend PostgreSQL/Redis (Python 3.15.2)`. This mismatch must be reconciled on the protected branch by competent owner after proof of Python3.15; never fake a 3.11 job or bypass branch protections.

New independent **FULL PRODUCT** review must use a separately materialized frozen review interface/hash and the existing `TS-WEB-INLINE-INDEPENDENT-REVIEW-BINDING-v0`: separate context, full-scope source review, **0 findings and 0 advisories**, original-result Library publication with file ID, byte count and checksum, original byte-identical Transport bridge, before any Product acceptance or merge. On failures, repair successor commit then retest/review; never retcon previous CI/IR. No production DB, retained Redis, credentials, deploy, staging or automatic issue closure.

## Known limits / pending

- PR #105 IR002 remained `NO_RECOMMEND / 0 findings / 1 LOW` due unbounded Python metadata; this composition deliberately changes the contract but is **NOT YET VALIDATED**.
- PR #83 historical Python3.15.2 successes and generated lock provenance are technical references, not an acceptance certificate for this subject. Native wheels and transitive compatibility must be installed anew.
- Legacy PostgreSQL sync Alembic URL uses a different driver than app asyncpg; do not remove psycopg2-binary merely because psycopg3 is present. Qualify the sync driver in fresh migrations.
- Original PR #101 browser failure `42386982010` remains historical `FAILURE / ROOT_CAUSE_UNKNOWN`; do not erase or explain it using unrelated CI.
- Do not close #43/#44 or PR #105 until exact Product integration and separate disposition. Do not merge this candidate without explicit immutable approval and ruleset/IR evidence.

## Initial exact CI attempt and bounded repair — R002

The initial composed candidate `93a90210ea000edf533a87aa86c3bc78398f9034`, tree `95d1ee6dceec0a22f875bd6edbc2a725697b0e9d`, launched one native attempt per existing PR workflow:

- [Issue43 bcrypt 42407934812](https://github.com/mauedgar/FitFlow/actions/runs/42407934812) completed FAILURE, backend **53 passed / 1 failed** on Python3.15.2; quality/frontend/compatibility PASS. The failing test introspected `app.routes` using a mutable `settings.API_V1_STR` prefix, which is not a reliable representation of installed HTTP routes after settings fixtures. Prior PR83 test source already exercised a stronger 405 HTTP contract.
- [FitFlow baseline 42407925273](https://github.com/mauedgar/FitFlow/actions/runs/42407925273) completed FAILURE: **386 passed / 3 failed**; failed assertions were that same users-router test, production class-session route precedence introspection with mutable `PREFIX`, and SQLAlchemy ORM `Mapped[T]` detection via raw `__annotations__` under Python 3.15 deferred annotations. Frontend job SUCCESS.
- [Schema 42407925644](https://github.com/mauedgar/FitFlow/actions/runs/42407925644) SUCCESS and [signed ADMIN browser 42407925331](https://github.com/mauedgar/FitFlow/actions/runs/42407925331) SUCCESS on initial SHA. These successes remain bound to the initial SHA and do not qualify a successor.

**R002 repair intent (tests only; no Product runtime changes):**

1. Replace the users-router negative route introspection with HTTP `PUT`/`PATCH` to registered paths `/users/register`, `/users/me` and `/users/public`, requiring HTTP 405, while explicitly checking route source declarations. This tests *real route exposure* and rejects an accidental 404 due to missing mounts. Preserve all current PR105 registration 72-byte/NUL test vectors, including `register-client`.
2. In the `/class-sessions/day` precedence test, compare immutable registered path suffixes rather than a mutable settings prefix; retain real HTTP negative control and actual `/day` request tests.
3. Use `inspect.get_annotations` instead of direct `__dict__['__annotations__']` for ORM `Mapped[T]` introspection compatible with Python3.15 deferred annotation semantics. No Booking model or domain schema changes.

The repair is a **new candidate identity**, not an attempt to relabel or rerun the failed initial workflows. It requires its own CI and later full IR; no Product acceptance, merge, retained data or file ownership expansion.

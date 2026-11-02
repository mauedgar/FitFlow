---
document_id: FF-ISSUE47-CANDIDATE-DOCIMPACT-20261102-002
status: CANDIDATE_PENDING_EXACT_FINAL_CI_AND_INDEPENDENT_REVIEW
date: 2026-11-02
scope: isolated_backend_quality_and_obsolete_ci_reference
acceptance: NOT_ACCEPTED
merge: NOT_AUTHORIZED
---

# FitFlow Issue #47 — bounded quality candidate and authority record

## Authority / identity

- Canonical Product baseline: `develop@c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`; `docs/SOURCE_OF_TRUTH.md` v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`.
- Original isolated repair: `quality/fitflow-backend-ruff-pyright-20261102-001@bbff13146684ebe323ff89de6d70e21fca5dfcd2`, tree `5706d0bbc5776fe1cc2174d412664ebc9eb001e1`; historical DocImpact `docs/quality/issue-47-docimpact-20261102.md` remains preserved.
- New Developer grant explicitly authorizes bounded nonsemantic Alembic lint repairs, CRUD/lock/fixture compatibility repairs, and removal/repair of obsolete references, with no Product acceptance or merge. This is a separate branch `quality/fitflow-issue47-migration-lint-20261102-002` derived from the original candidate, not a restart of its terminal automation.
- No changes to `develop`, PR #46, #45, #42, Issue #43 auth implementation, staging #37, secrets or real data. No new TaskCycle.

## Measured repair

- Initial Ruff/Pyright baseline: **201 / 38**. Original safe repair: **68 / 17**. This branch repairs remaining Alembic and backend source diagnostics; exact intermediate full gate below reports **Ruff PASS / Pyright 0 errors**.
- Alembic: Ruff 0.17.3 safe-only preview [Actions 41395155191](https://github.com/mauedgar/FitFlow/actions/runs/41395155191) changed 15 migration/environment files; 17 migration revision files remain present with the same revision/down_revision/branch_labels/depends_on values and upgrade/downgrade operation AST. An unused `bind` assignment became an equivalent `op.get_bind()` expression, preserving the connection call. No revision, DDL, migration identity, or ordered operation removed. Full intermediate [AST/graph gate](https://github.com/mauedgar/FitFlow/actions/runs/41395867829) passed and disposable PostgreSQL 15 Alembic upgrade head passed. No real DB SQL was executed.
- Non-Alembic Ruff: safe-only preview [Actions 41395414182](https://github.com/mauedgar/FitFlow/actions/runs/41395414182) repaired 3 diagnostics; ORM `__mapper_args__` now uses immutable `MappingProxyType` compatible with SQLAlchemy declarative mapping (no `ClassVar` incompatible workaround); unused time variable removed; test annotation introspection uses `inspect.get_annotations`.
- Pyright: specialized CRUD `get` overrides now accept base `obj_id: object` and optional `options` while preserving specialized relation flags; `update` accepts the base schema/dict union with password hashing and capacity validation; ClassSchedule `remove` supports both existing ID lookup and base `db_obj` contract, with hard-delete-by-ID rejected. PostgreSQL row-lock `of` uses mapped ID columns, and SQL compilation tests preserve `FOR UPDATE OF users, persons, clients`. Fixtures use actual ORM/AsyncSession types or explicit negative-case instrumentation; one newly added localized Pyright exception documents Pydantic BaseSettings' dynamic `_env_file` signature; older targeted suppressions elsewhere remain separately owned. Two obsolete blanket `# pyright: ignore-all` directives were removed from CRUDUser and CRUDTeacher.
- Obsolete CI reference: [update-schema.yml](https://github.com/mauedgar/FitFlow/blob/quality/fitflow-issue47-migration-lint-20261102-002/.github/workflows/update-schema.yml) previously used nonresolving `astral-sh/setup-uv@v10` (failed Actions 41395224239 and 41395238702); replaced by immutable v10.3.3 commit `68559e99cc807c1eb7e9238fd43a15bba460eec2`. Isolated [uv smoke 41396002469](https://github.com/mauedgar/FitFlow/actions/runs/41396002469) PASS (`uv 0.13.6`). The complete schema auto-commit workflow is **not** thereby qualified; no schema commit was authorized.

## CI qualification and limits

- [Full intermediate gate Actions 41395867829](https://github.com/mauedgar/FitFlow/actions/runs/41395867829), subject `87186a94d5421a3b57458fe45295df2f97ecb602`: migration graph/operation AST PASS (17 revision files), disposable PG15 Alembic upgrade PASS, Ruff 0.17.3 **all checks passed**, Pyright 1.1.414 **0 errors / 0 warnings**, backend **245 passed, 1 warning** (Passlib `crypt` deprecation). This gate is evidence for that exact intermediate SHA, **not** a PASS automatically transferred to the final DocImpact commit.
- Additional CRUD override/negative-case regression tests and CI reference pin were committed after that intermediate gate. Final candidate must undergo **new exact-SHA/tree** validation from a separate CI-only branch after temporary workflow cleanup; no prior PASS is transferable.
- The inherited Passlib deprecation remains owned by Issue #43 and is not suppressed. PR #46 independent IR003 still has three advisories including real staging TLS (#37), auth warning (#43), and quality requalification (#47); separate branch results do not resolve those automatically.
- Independent WEB_INLINE IR must review the exact final candidate, including migration history, ORM mapping, CRUD contract, negative tests, row-lock SQL, and CI pin, in a context separate from implementation. Developer acceptance threshold remains **0 findings / 0 advisories**. No acceptance, merge, PR ready-for-review, or issue closure is authorized by this document.

---
document_id: FF-ISSUE47-DOCIMPACT-20261102-001
status: CANDIDATE_PENDING_INDEPENDENT_REVIEW
date: 2026-11-02
scope: isolated_backend_quality
acceptance: NOT_ACCEPTED
merge: NOT_AUTHORIZED
---

# DocImpact — FitFlow Issue #47, bounded quality repair

## Authority and immutable provenance

- Product baseline remains `develop@c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`, SOT v5.3 blob `f36307af0777fd3b493792ad42115fec56ac44b3`.
- Isolated implementation branch: `quality/fitflow-backend-ruff-pyright-20261102-001`; original terminal baseline `bbff13146684ebe323ff89de6d70e21fca5dfcd2`, tree `5706d0bbc5776fe1cc2174d412664ebc9eb001e1`.
- Developer grant (2026-11-02): nonsemantic Alembic historical lint corrections and CRUD override/lock/fixture type repairs; preserve migration graph, SQL/DDL, booking concurrency, authentication and existing consumers. No Product merge or acceptance without 0 findings / 0 advisories from independent WEB_INLINE IR.
- Pre-DocImpact validated code subject `e8dae016024a22e809c9a7fafb904b558ba1d210`, tree `7f032d4fb51071f58e473042413c6b7b1305dcf9`, exact-subject [Actions 41398665968](https://github.com/mauedgar/FitFlow/actions/runs/41398665968) **completed/success** across static quality, backend regression and migration invariants. This result is **not** transferable to a new SHA after this documentation edit. Final exact-SHA validation must be repeated.
- No changes to `develop`, PR #46/#45/#42, Issue #43 authentication implementation, staging #37, dependency locks, migration revision identities, or real user state. Temporary implementation workflows were removed from the implementation branch.

## Baseline and measured repair

| Exact subject | Ruff 0.17.3 | Pyright 1.1.414 | Backend |
| --- | ---: | ---: | --- |
| Original develop | 201 | 38 | previous 243 PASS |
| Initial isolated candidate `bbff131` | 68 | 17 | 243 PASS, 1 inherited warning |
| Corrected pre-document candidate `e8dae016` | **0** | **0** | **253 PASS**, 1 inherited Passlib `crypt` warning |

- [Quality job 125125471901](https://github.com/mauedgar/FitFlow/actions/runs/41398665968/job/125125471901): Ruff **All checks passed**; Pyright **0 errors, 0 warnings, 0 informations**. Pinned test requirements installed before type analysis; no invalid missing-dependency diagnostic.
- [Backend job 125125471766](https://github.com/mauedgar/FitFlow/actions/runs/41398665968/job/125125471766): isolated PostgreSQL 15/Redis 7, Alembic upgrade head, **253 pytest PASS**, **1 inherited warning**. Includes 10 new regression tests. This is not staging, real DB, TLS or browser E2E.
- [Migration-invariants job 125125471554](https://github.com/mauedgar/FitFlow/actions/runs/41398665968/job/125125471554): historical migration file set unchanged, `revision/down_revision/branch_labels/depends_on` identities preserved, and AST upgrade/downgrade call graphs unchanged. All migrations upgraded on a disposable CI DB; **no downgrade was run** and no real DB touched.
- `git diff --check` passed. The source diff from `bbff131` changes 35 backend paths: 15 Alembic files, 19 existing backend source/test files, and one new contract test. No final workflow changes.

## Design and compatibility review targets

1. Alembic: Ruff safe-only import/type/no-op corrections; `op.get_bind()` call preserved when removing an unused binding. Historical revisions and ordered DDL/upgrade/downgrade calls preserved. No migration deletion or data reset.
2. ORM: three localized `# noqa: RUF012` for SQLAlchemy `__mapper_args__` dict literals, each with rationale: `ClassVar` was previously incompatible with `DeclarativeBase`; retain runtime dictionary semantics. These are narrow false-positive dispositions, not blanket exclusions or a claim that all future lint is waived.
3. CRUD: specialized `get` overrides retain base `obj_id: object` and `options` keyword compatibility, preserving existing relation-loading defaults. `CRUDClassSchedule.remove` accepts both existing `obj_id` and base `db_obj/hard` contracts. User and schedule `update` accept base dict input without changing valid Pydantic update behavior; new invalid input handling requires reviewer attention.
4. Concurrency: `with_for_update(of=(User.id, Person.id, Client.id))` preserves PostgreSQL table lock targets `users, persons, clients`, verified by regression compilation test. No lock removal, transactional boundary changes or booking admission-policy edits.
5. Fixtures: type-correct SQLAlchemy `AsyncSession` and ORM objects replace structural test fakes where appropriate; negative HTTP/Redis tests remain exercised. New `test_crud_override_contract.py` checks substitutability, mapper identity and row-lock targets.

## Independent gates and unresolved external advisories

- **WEB_INLINE IR on final exact SHA/tree is still NOT_RUN**; static green and 253 tests do not constitute independent acceptance. Product acceptance, merge, Issue closure and SOT update remain prohibited.
- Issue #43 owns inherited Passlib `crypt` warning / bcrypt hash compatibility. No auth dependency change, user hash rewrite or warning suppression was performed.
- PR #46 IR003 A02 remains real staging TLS qualification, owned by Issue #37; synthetic TLS proof cannot be transferred to this Product candidate.
- Separate CI workflow `.github/workflows/update-schema.yml` references unavailable `astral-sh/setup-uv@v10`; triggered [Actions 41397971513](https://github.com/mauedgar/FitFlow/actions/runs/41397971513) failed in job setup **before migrations or schema dump**, independently of the successful exact-candidate backend/migration checks. Verified tag `v10.3.3` exists, but changing schema auto-commit authority or CI workflow requires a separate reviewed scope. Do not claim this workflow PASS or silently enable writes to `develop`.
- No deployment-equivalent TLS, full E2E or credential-backed staging proof. These are distinct Product gates, not excused by static-quality green.

## Disposition

`CANDIDATE_PENDING_INDEPENDENT_REVIEW` — technical-quality target achieved on the pre-document code subject, but **final SHA/tree requalification and independent WEB_INLINE IR are required** before any acceptance recommendation. Keep Issue #47 OPEN and branch isolated; never infer 0 global advisories from Ruff/Pyright green.

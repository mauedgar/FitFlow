---
document_id: FF-ISSUE47-DOCIMPACT-20261102-001
status: BLOCKED_SCOPED
date: 2026-11-02
scope: isolated_backend_quality
acceptance: NOT_ACCEPTED
merge: NOT_AUTHORIZED
---

# DocImpact — FitFlow Issue #47, isolated backend quality

## Authority and provenance

- Product baseline: `develop@c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`, SOT v5.3.
- Exclusive repair branch: `quality/fitflow-backend-ruff-pyright-20261102-001`.
- Validated source before removing the temporary diagnostic workflow: `850c17522d515bc9979dd0b3b20bc1ba96797b9c`, tree `1a0bfae2cb89d7114740be29421a511c8d866a54`.
- Quality and backend run: https://github.com/mauedgar/FitFlow/actions/runs/41388523380
- No Product acceptance, merge, close, migration ownership transfer, dependency version change, or additional TaskCycle.

## Diagnostic evolution (Ruff 0.17.3 / Pyright 1.1.414)

| Subject | Ruff findings | Pyright errors | Qualification |
| --- | ---: | ---: | --- |
| Original develop | 201 | 38 | Baseline FAIL |
| Safe-fix / restored Alembic, installed test dependencies | 109 | 38 | Diagnostic FAIL |
| Repair source 850c175 | 68 | 17 | Quality FAIL; not a green gate |

The original Pyright result of 331 without installed backend requirements was an invalid environment diagnostic and is excluded. All figures above use installed dependencies. The quality job `125094602029` intentionally fails on remaining errors, rather than masking them.

### Ruff residual: 68

- **59** in protected `backend/alembic/env.py` and `backend/alembic/versions/**`. All migration files are byte-preserved relative to `develop`; fixing these requires a distinct Product/migration-owner grant.
- **9** outside Alembic: three ORM `__mapper_args__` RUF012; one schema import I001; one router empty comment PLR2044; one Pydantic class pass PIE790; one unused `now` F841; two metadata-test introspection RUF063. These are not hidden or suppressed. A ClassVar-only experiment created a Pyright ORM-base incompatibility, so it was reverted without changing mapper semantics.

### Pyright residual: 17

- **10** incompatible overrides between generic `CRUDBase` and specialized CRUD methods (`get`, `update`, `remove`).
- **1** SQLAlchemy `with_for_update(of=(User, Person, Client))` typing diagnostic; the lock semantics are preserved unchanged.
- **6** test typing issues: `Settings(_env_file=None)`, one `FakeSession`, and four `SimpleNamespace`/object arguments in Client projection tests.

Do not narrow base method contracts, widen specialized CRUD APIs, change lock targets, or cast away diagnostics without an independently reviewed Product-compatible design. No bulk ignores, mass exclusions, or test removal.

## Validation and compatibility

- Python 3.11.17, pinned backend test requirements, isolated ephemeral PostgreSQL/Redis services in GitHub Actions, no real DB/secrets/local Docker.
- Backend job `125094602015` on exact code SHA `850c175`: **243 passed**, **1 pre-existing DeprecationWarning** from Passlib importing Python `crypt` (no failures). This is test PASS, not quality PASS.
- The diff against baseline has **zero Alembic changes**, **zero requirements/lock changes**; auth, booking, and concurrency behavior is not intentionally modified. Dependency metadata in FastAPI uses standard `Annotated` declarations; full backend HTTP/auth/booking suite passed.
- A final exact-SHA/tree deterministic runner must be evaluated separately after this DocImpact and workflow cleanup commit; prior test PASS must not be transferred to a new SHA.

## Disposition

**BLOCKED_SCOPED / 0F-0A NOT MET.** Migration ownership and independently reviewed CRUD/type-contract decisions are required before quality can become green. The residual 1 Passlib deprecation warning also remains an advisory, not suppressed. No independent WEB_INLINE reviewer was launched because no sufficient 0F/0A candidate exists.

This document is branch-local impact evidence. It does not revise canonical SOT or authorize integration.

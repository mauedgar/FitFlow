---
artifact: VALIDATION
task_id: FF-IMP-001
run_id: FF-IMP-001-20260825-01
date: 2026-08-25
baseline: 5cfcd28b7c2aa0d0e871b72036bdfa4fe59e3827
status: FAIL
change_scope_status: PASS
next_state: REVIEWING
---

# Alcance

Validacion determinista de `FF-IMP-001` sobre Compose aislado
`fitflow-ff-imp-001` y ejecucion adicional del wrapper canonico `fitflow-test`.
No se leyo ni modifico `.env`, no se aplicaron migraciones y la DB nueva se
conservo sin `alembic_version`.

# Gates

| Gate | Comando | CWD | Exit | Estado | Salida verificable |
| --- | --- | --- | ---: | --- | --- |
| Build limpio | `docker compose --project-name fitflow-ff-imp-001 --file docker-compose.test.yml build --no-cache backend_test` | worktree root | 0 | PASS | imagen con Pydantic 2.11.7, Ruff 0.16.4 y Pyright 1.1.411 |
| Startup y OpenAPI | `... exec --no-TTY backend_test python -c "from app.main import app; schema=app.openapi(); ..."` | worktree root | 0 | PASS | 91 rutas, OpenAPI 3.1.0, 71 paths |
| Collection | `... python -m pytest --collect-only -q tests` | worktree root | 0 | PASS | 44 tests recolectados; cero errores |
| Dirigidos | `... python -m pytest tests/smoke/test_pytest_harness.py tests/smoke/test_schema_startup.py tests/unit/test_orm_metadata.py tests/unit/test_redis_client.py tests/unit/test_pydantic_contracts.py tests/unit/test_rrule_schedule.py tests/unit/test_booking_lifecycle.py tests/unit/test_allowed_plan_access.py` | worktree root | 0 | PASS | 38 passed |
| Contratos schemas | `... python -m pytest tests/smoke/test_schema_startup.py tests/unit/test_pydantic_contracts.py tests/unit/test_rrule_schedule.py` | worktree root | 0 | PASS | 10 passed |
| RRULE integration | `... python -m pytest tests/integration/test_rrule_generation.py` | worktree root | 1 | FAIL | 2 failed por `relation gym_classes does not exist` |
| Booking integration | `... python -m pytest tests/integration/test_booking_database_invariants.py` | worktree root | 1 | FAIL | 4 failed por `relation users does not exist` |
| Suite completa | `... python -m pytest tests` | worktree root | 1 | FAIL | 38 passed, 6 failed; los seis requieren tablas inexistentes |
| Estado DB | `... postgres_test psql ... -tAc "SELECT to_regclass('public.alembic_version'), to_regclass('public.users');"` | worktree root | 0 | PASS | ambos valores vacios; DB nueva no inicializada |
| Alembic topology | `... backend_test alembic heads` | worktree root | 0 | PASS | `e4f5a6b7c8d9 (head)` |
| Ruff scope local | `.venv_backend/Scripts/python.exe -m ruff check <cinco paths modificados>` | backend | 0 | PASS | `All checks passed!` |
| Ruff scope Docker raw | `... python -m ruff check <cinco paths modificados>` | worktree root | 1 | FAIL | solo 5 `EXE002`; BuildKit Windows marca COPY como ejecutable aunque Git conserva 100644 |
| Ruff scope Docker normalizado | `... python -m ruff check --ignore EXE002 <cinco paths modificados>` | worktree root | 0 | PASS | `All checks passed!` |
| Ruff global | `... python -m ruff check .` | worktree root | 1 | FAIL | 274 hallazgos baseline/out-of-scope, incluido EXE002 repo-wide |
| Pyright scope | `... pyright <cinco paths modificados>` | worktree root | 0 | PASS | 0 errors, 0 warnings, 0 informations |
| Pyright global | `... pyright .` | worktree root | 1 | FAIL | 35 errores baseline/out-of-scope; ninguno en paths cambiados |
| Wrapper canonico | `powershell.exe -ExecutionPolicy Bypass -File scripts/quality/run_backend_validation.ps1` | worktree root | 1 | FAIL | reproduce suite DB FAIL, Ruff 274 y Pyright 35 |
| Diff whitespace | `git diff --check` | worktree root | 0 | PASS | sin errores; avisos LF/CRLF no alteran contenido |
| Orca Compose | `docker compose --file docker-compose.test.yml config --quiet` | worktree root | 0 | PASS | nombre Compose valido; setup copia `backend/.env` sin versionar su contenido |

# Interpretacion

El cambio task-scoped es `PASS`: startup, OpenAPI, collection, contratos,
Ruff dirigido y Pyright dirigido no presentan regresiones. El estado global es
`FAIL` porque las reglas exigen conservar como tales los seis tests DB, Ruff
global, Pyright global y el wrapper. La DB nueva carece de tablas y
`alembic_version`; no se aplicaron migraciones porque estan prohibidas en esta
task.

El Developer autorizo incluir `orca.yaml` en el mismo commit. Su cambio se
limita a copiar `backend/.env` al worktree; la referencia
`docker-compose.test.yml` fue validada y el contenido de `.env` no fue leido,
modificado ni versionado.

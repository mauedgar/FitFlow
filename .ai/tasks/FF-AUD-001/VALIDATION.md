---
artifact: VALIDATION
task_id: FF-AUD-001
run_id: FF-AUD-001-20260825-01
date: 2026-08-25
baseline: 20d26166e5b5a4166eecf95833c18036aae6dc06
status: PASS
product_baseline: FAIL
next_state: PENDING_ACCEPTANCE
---

# Alcance

Validacion determinista del baseline actual de Sprint 6.8. Se uso
exclusivamente Compose `fitflow-test`, PostgreSQL `fitflow_test` y Redis de test.
No se leyo ni modifico `.env`, no se uso la DB de desarrollo y no se aplicaron
migraciones.

# Gates

| Gate | Comando | CWD | Estado | Salida verificable |
| --- | --- | --- | --- | --- |
| Git baseline | `git status --short --branch && git rev-parse HEAD && git merge-base HEAD develop` | root | PASS | branch `feat/FF-AUD-001`; HEAD y merge-base `20d2616`; solo bundle de la task sin trackear |
| Docker | `docker version` | root | PASS | cliente y engine `29.7.2` disponibles |
| Suite canonica | `powershell.exe -ExecutionPolicy Bypass -File scripts/quality/run_backend_validation.ps1` | root | FAIL | pytest recolecta 10 items y aborta con 6 errores de import circular |
| Smoke | `docker compose --project-name fitflow-test --file docker-compose.test.yml exec --no-TTY backend_test python -m pytest tests/smoke -m smoke` | root | PASS | `2 passed` |
| ORM metadata | `... python -m pytest tests/unit/test_orm_metadata.py` | root | PASS | `7 passed`; 9 tablas y mappers configurables |
| Redis | `... python -m pytest tests/unit/test_redis_client.py` | root | PASS | `1 passed` |
| Startup/import | `... python -c "from app.main import app; print(len(app.routes))"` | root | FAIL | `ImportError` por `class_schedule -> gym_class -> class_schedule` |
| Alembic head | `... alembic heads` | root | PASS | head unico `e4f5a6b7c8d9` |
| Alembic history | `... alembic history` | root | PASS | cadena lineal de 16 revisiones desde base hasta head |
| Metadata directa | `... python -c "from app.db.base import Base; ..."` | root | PASS | 9 tablas activas |
| Compilacion | `... python -m compileall -q app alembic` | root | PASS | exit code 0 |
| Ruff | wrapper canonico | root | UNAVAILABLE | Ruff no esta instalado en `backend_test` |
| Pyright | wrapper canonico | root | UNAVAILABLE | Pyright no esta instalado en `backend_test` |
| Integration | `tests/integration` | root | NOT_RUN | collection bloqueada por import circular antes de ejecutar tests |
| API | `tests/api` | root | NOT_RUN | no existen tests ejecutables; solo plantilla bajo `_templates` |
| Concurrency | `tests/concurrency` | root | NOT_RUN | no existen tests ejecutables; solo plantilla bajo `_templates` |
| Upgrade/downgrade | Alembic sobre `fitflow_test` | root | NOT_RUN | fuera del scope; tres downgrades declaran `NotImplementedError` |
| JSON syntax | `node -e` con `JSON.parse` sobre los cuatro artefactos | root | PASS | `validation`, `review`, `result` y `run-state` parsean correctamente |
| JSON Schema engine | Draft 2020-12 | root | UNAVAILABLE | `jsonschema`, `pwsh/Test-Json` y un validador local no estan disponibles; no se instalaron dependencias |

# Fallo reproducible principal

La suite y el startup importan esta cadena:

```text
app.main
-> schemas.user
-> schemas.teacher
-> schemas.class_schedule
-> schemas.gym_class
-> schemas.class_schedule (parcialmente inicializado)
```

Evidencia fuente:

- `backend/app/schemas/user.py:140-144` importa y reconstruye `TeacherPublic`;
- `backend/app/schemas/teacher.py:17` importa `ClassSchedulePublic`;
- `backend/app/schemas/class_schedule.py:22` importa schemas de `gym_class`;
- `backend/app/schemas/gym_class.py:21` vuelve a importar `ClassSchedulePublic`;
- `backend/app/schemas/gym_class.py:118` usa ese tipo en la respuesta publica.

# Extractos de salida

## Suite canonica

```text
collected 10 items / 6 errors
ERROR tests/integration/test_booking_database_invariants.py
ERROR tests/integration/test_rrule_generation.py
ERROR tests/unit/test_allowed_plan_access.py
ERROR tests/unit/test_booking_lifecycle.py
ERROR tests/unit/test_pydantic_contracts.py
ERROR tests/unit/test_rrule_schedule.py
Interrupted: 6 errors during collection
```

Los seis errores terminan en:

```text
ImportError: cannot import name 'ClassSchedulePublic' from partially
initialized module 'app.schemas.class_schedule'
```

## Gates dirigidos

```text
tests/smoke/test_pytest_harness.py ..                    2 passed
tests/unit/test_orm_metadata.py .......                  7 passed
tests/unit/test_redis_client.py .                        1 passed
alembic heads                                            e4f5a6b7c8d9 (head)
metadata tables                                          9
compileall                                               exit 0
Ruff                                                     UNAVAILABLE
Pyright                                                  UNAVAILABLE
```

# Cobertura y limitaciones

- `docker-compose.test.yml:27-36` proporciona configuracion de test sin `.env`;
- `docs/quality-and-validation.md:29-39` declara los wrappers usados;
- `backend/pytest.ini:8-14` declara suites API y concurrency, pero no existen
  archivos ejecutables en esos directorios;
- no se ejecutaron migraciones, fixes ni cambios de producto;
- los JSON v2 tienen sintaxis valida y referencias hash verificadas; la
  validacion completa contra Draft 2020-12 permanece `UNAVAILABLE`;
- `FAIL` describe el baseline observado y no invalida los gates dirigidos que
  si alcanzaron `PASS`.

# Resultado

`PASS` para la ejecucion del protocolo de auditoria: los comandos y sus estados
quedaron registrados de forma reproducible. El baseline de producto es `FAIL`
por la suite amplia y startup. Gate 2 puede declararlo `KNOWN`; Gate 3 no
autoriza cambios DB/ORM/migraciones/dominio con esta evidencia solamente.

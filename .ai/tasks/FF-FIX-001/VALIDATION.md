---
artifact: VALIDATION
task_id: FF-FIX-001
run_id: FF-FIX-001-20260825-01
date: 2026-08-25
status: FAIL
change_scope_status: PASS
global_validation_status: FAIL
---

# Validacion

## Entorno

`fitflow-test` reconstruido con el diff (`docker compose up --build --detach`).
Por decision expresa del Developer, Gate 3 se levanto UNICAMENTE para
inicializar la DB desechable `fitflow_test`; no se tocaron DB dev/prod ni se
autoraron migraciones.

## Gates task-scoped (todos PASS)

| Gate | Resultado | Evidencia |
| --- | --- | --- |
| test-db-init | PASS | `alembic upgrade head` -> `e4f5a6b7c8d9`; `users` y `gym_classes` presentes |
| startup-import | PASS | `import app.main`: 91 rutas, exit 0 |
| directed-integration | PASS | `test_rrule_generation.py`: **2 passed en 9.12s** (primera vez verdes sobre DB real) |
| unit-metrics | PASS | nuevo `test_schedule_metrics.py`: 4 passed |
| full-suite | PASS | **48 passed, 0 failed** (baseline previo: 38 passed / 6 failed) |
| pyright-changed | PASS | 0 errors, 0 warnings en los 4 archivos del scope |
| ruff-diff-lines | PASS | cero hallazgos en lineas modificadas (`:93`, `:226`, `:276`, `:294`, llamadas de test) |

## Gates globales (FAIL preexistente, no atribuible al diff)

| Gate | Resultado | Detalle |
| --- | --- | --- |
| ruff-files | FAIL | 16 hallazgos en lineas NO modificadas de archivos propios: EXE002 x4 (artefacto Windows; incluye al archivo nuevo), I001, RUF100 x7, DTZ011 x2 (llamadas `date.today()` previas), F401 x2 |
| ruff-global | FAIL | observado 275-276 entre corridas (+delta vs 274 por artefacto EXE002 entre worktrees) |
| pyright-global | FAIL | 29 errores; **mejora -6 vs baseline 35**, atribuible al fix int de `capacity_snapshot` |
| canonical-wrapper | FAIL | pytest 48 passed; cae solo por deuda global |

## Notas

- Los dos tests RRULE que el review de FF-IMP-001 predijo rotos por TypeError
  pasan con el fix: la prediccion F1 queda cerrada empiricamente.
- Pyright global mejora de 35 a 29: el acceso `.get("capacity")` sobre int que
  el fix elimina era fuente real de errores de tipo.
- No se amplio scope para limpiar el lint preexistente de archivos propios
  (DTZ011 implicaria cambiar semantica horaria; EXE002 es artefacto de
  filesystem). Queda registrado como follow-up opcional.

Veredicto: validacion task-scoped PASS; estado global FAIL por deuda
documentada. Detalle completo en `.ai/runs/FF-FIX-001-20260825-01/validation.json`.

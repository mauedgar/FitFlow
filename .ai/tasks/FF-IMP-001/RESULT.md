---
artifact: RESULT
task_id: FF-IMP-001
run_id: FF-IMP-001-20260825-01
date: 2026-08-25
status: COMPLETED
workflow_state: PENDING_ACCEPTANCE
change_scope_status: PASS
global_validation_status: FAIL
---

# Resultado

El ciclo `class_schedule <-> gym_class` fue eliminado mediante registros
`*_refs.py`, sin imports tardios o condicionales y sin modificar DB, ORM,
migraciones, dominio, dependencias ni consumidores.

El flujo resultante es aciclico:

```text
base/enums -> gym_class_refs -> class_schedule_refs -> class_schedule
                              -> gym_class
gym_class_refs -------------------------------------> gym_class
```

`app.schemas.class_schedule` y `app.schemas.gym_class` conservan los nombres
publicos por reexportacion. Los contratos movidos preservan campos, defaults,
constraints, MRO y `model_config`.

# Criterios

| Criterio | Estado | Evidencia |
| --- | --- | --- |
| AC-1 startup | PASS | `app.main` importa; 91 rutas |
| AC-2 collection | PASS | 44 tests, cero errores de import |
| AC-3 contratos/RRULE/Booking | PASS | 38 dirigidos pasan; seis integraciones se ejecutan y fallan solo por DB sin tablas |
| AC-4 OpenAPI | PASS | OpenAPI 3.1.0, 71 paths |
| AC-5 smoke/ORM/Redis/allowed-plan | PASS | incluidos en 38 passed |
| AC-6 Ruff/Pyright/Alembic | PASS | scope cambiado limpio; globales FAIL registrados; head `e4f5a6b7c8d9` |
| AC-7 fronteras | PASS | sin cambios DB, ORM, migraciones ni dominio |
| AC-8 independencia | PASS | Validator y Reviewer independientes; review final PASS |

# Validacion global

El wrapper canonico permanece `FAIL`: suite completa `38 passed, 6 failed` por
DB nueva sin tablas, Ruff global 274 y Pyright global 35. Ningun resultado se
promueve a PASS por inferencia. Las migraciones no se ejecutaron; la ausencia de
`alembic_version` se registra como DB no inicializada, no como drift.

# Doc Sync

- `FF-AUD-001` esta integrada en `develop`, pero sus vistas historicas siguen
  indicando `PENDING_ACCEPTANCE`/`NOT_INTEGRATED`; la diferencia se registro
  append-only en TASK sin reescribir evidencia;
- no se requiere cambio en documentacion canonica ni ADR;
- el Developer autorizo incluir `orca.yaml` en este commit; copia
  `backend/.env` hacia el worktree y conserva la referencia valida
  `docker-compose.test.yml`;
- el contenido de `.env` no fue leido, modificado ni agregado a Git.

# Contratos de evidencia

AJV Draft 2020-12 con `ajv-formats` valido `task.json`, `validation.json`,
`review.json`, `result.json` y `run-state.json` contra sus schemas v2; los cinco
comandos terminaron con exit code 0 desde el worktree root.

# Veredicto

Implementacion task-scoped `PASS`, review independiente `PASS`, run
`COMPLETED` en `PENDING_ACCEPTANCE`. No se hizo commit, push o merge. Solo el
Developer puede aceptar, integrar y promover a `DONE`.

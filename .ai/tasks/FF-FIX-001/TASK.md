---
artifact: TASK
task_id: FF-FIX-001
title: Restaurar contrato de generacion de sesiones y consumo de capacity_snapshot
status: PENDING_ACCEPTANCE
task_type: FIX
scope: backend
lane: ai_orchestrated
risk: medium
priority: P0
branch: fix/FF-FIX-001-session-contract
baseline: 78aaa3082d079f39a2bd8da015cc165a81b5cc20
depends_on: FF-IMP-001
ownership_keys:
  - path:.ai/tasks/FF-FIX-001/**
  - path:.ai/runs/FF-FIX-001-*/**
  - path:backend/app/routers/class_schedules.py
  - path:backend/app/services/class_schedule_service.py
  - path:backend/tests/integration/test_rrule_generation.py
  - path:backend/tests/unit/test_schedule_metrics.py
read_scope:
  - backend/app/services/class_schedule_service.py
  - backend/app/db/models/class_session.py
  - backend/app/schemas/class_session.py
  - docker-compose.test.yml
---

# Objetivo

Alinear todos los puntos de llamada de `generate_sessions_for_schedule` a su
firma keyword-only vigente (`schedule_id`, `window_start`, `window_end`, `db`)
y corregir el consumo de `capacity_snapshot` como dict cuando el modelo lo
define como `int`, restaurando las rutas POST create y PUT regenerate.

# Origen

- Finding F1 (HIGH) del review independiente post-aceptacion de `FF-IMP-001`:
  TypeError determinista en `routers/class_schedules.py:93,226` y en
  `tests/integration/test_rrule_generation.py:63-68,124-126`.
- Finding F3 (MEDIUM-HIGH): acceso `.get("capacity")` sobre un `int`
  (`class_schedule_service.py:276,294`); el test de integracion aserta
  `capacity_snapshot == 7`.
- Decision del Developer (2026-08-25): autoriza la task, integra F3 en ella y
  levanta Gate 3 unicamente para inicializar `fitflow_test`.

# Alcance

- convertir a keyword args las llamadas en routers y test de integracion;
- eliminar el argumento fantasma `current_user`/`None` (el servicio nunca lo
  uso; no se restaura el parametro);
- aritmetica int para `capacity_snapshot` en `get_schedule_occupancy` y
  `get_schedule_next_session`;
- inicializar `fitflow_test` con `alembic upgrade head` (DB desechable) para
  validacion real de integracion;
- producir evidencia v2 y detener el run en `PENDING_ACCEPTANCE`.

# Fuera de alcance

- autorar o modificar migraciones; DB de desarrollo/produccion;
- deuda global Ruff 274 / Pyright 35 (solo gates task-scoped);
- imports diferidos de `client.py`/`user.py` (follow-up opcional separado);
- frontend, dominio, dependencias, secretos, commits/push/merge finales.

# Criterios de aceptacion

- [x] AC-1: `import app.main` exit 0 en `fitflow-test` post-cambio.
- [x] AC-2: `alembic upgrade head` deja `fitflow_test` en `e4f5a6b7c8d9` con
      tablas `users` y `gym_classes` presentes.
- [x] AC-3: `pytest tests/integration/test_rrule_generation.py` verde
      (generacion e idempotencia + solapamiento rechazado).
- [x] AC-4: suite completa en `fitflow-test` sin fallos atribuibles al diff
      (los 6 fallos previos por tablas desaparecen).
- [x] AC-5: consumo int de `capacity_snapshot` verificado por test unitario o
      integracion dirigido (occupancy/next-session no crashean).
- [ ] AC-6: Ruff y Pyright task-scoped limpios en los tres archivos tocados
      (resultado: Pyright PASS con 0 errores; Ruff FAIL solo por 16 hallazgos
      legacy en lineas no modificadas — cero atribuibles al diff; ver
      VALIDATION.md).
- [x] AC-7: diff restringido a ownership keys; sin DB/ORM/migraciones/dominio.
- [x] AC-8: Validator y Reviewer independientes con evidencia registrada.

# Documentos requeridos

- `AGENTS.md`;
- `docs/SOURCE_OF_TRUTH.md`;
- `docs/process/task-lifecycle-and-reporting.md`;
- `docs/process/risk-and-parallelism.md`;
- `docs/quality-and-validation.md`;
- artefactos `FF-AUD-001` y `FF-IMP-001` como contexto.

# Enmienda de alcance

- 2026-08-25 — AC-5 requerido verificacion durable; se agrega unit test
- `backend/tests/unit/test_schedule_metrics.py` y su ownership key.

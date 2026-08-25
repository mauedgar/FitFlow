---
artifact: PLAN
task_id: FF-FIX-001
run_id: FF-FIX-001-20260825-01
date: 2026-08-25
baseline: 78aaa3082d079f39a2bd8da015cc165a81b5cc20
risk: medium
---

# Plan

## Ruta

`PLAN -> ROUTE -> EXPLORE -> EXECUTE -> VALIDATE -> REVIEW -> DOC_SYNC ->
PENDING_ACCEPTANCE`.

## Particion de escritura (sin interseccion)

| Rol | Archivos | Cambio |
| --- | --- | --- |
| coder_a | `backend/app/routers/class_schedules.py` | llamadas keyword-only en `:93` y `:226`, sin `current_user` en la llamada al servicio |
| coder_a | `backend/app/services/class_schedule_service.py` | `capacity_snapshot` como int en `get_schedule_occupancy` y `get_schedule_next_session` (`:276`, `:294`) |
| coder_b | `backend/tests/integration/test_rrule_generation.py` | 4 llamadas a keyword-only con `schedule_id=schedule.id`, sin `None` fantasma |

## Decisiones de diseno

1. No se restaura el parametro `current_user`: el servicio nunca lo uso
   (`grep` vacio en `class_schedule_service.py`); restaurarlo seria regresar a
   la API muerta previa.
2. Se pasa `schedule.id` (UUID) directamente; `str(...)` innecesario frente a
   la firma tipada.
3. Fallback defensivo para snapshots legacy int/None via `or 0`.
4. Gate 3 levantado SOLO para `fitflow_test` (DB desechable); prohibido tocar
   dev/prod y prohibido autorar migraciones.

## Validacion

1. `docker compose -f docker-compose.test.yml -p fitflow-test up -d --build backend_test db_test`
2. `alembic upgrade head` contra `fitflow_test`; verificar `alembic_version ==
   e4f5a6b7c8d9` y presencia de `users`/`gym_classes`.
3. `pytest tests/integration/test_rrule_generation.py -m integration`
4. Suite completa del wrapper canonico; comparar contra baseline
   `38 passed / 6 failed`.
5. Ruff + Pyright task-scoped sobre los tres archivos.
6. Reviewer independiente.

## Criterio de parada

Detener en `PENDING_ACCEPTANCE`. Sin push ni merge; solo el Developer integra.

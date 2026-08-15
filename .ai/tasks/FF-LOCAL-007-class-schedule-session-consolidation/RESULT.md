---
id: FF-LOCAL-007
title: Consolidar ClassSchedule y ClassSession
status: Validation
area: backend
execution_lane: codex
type: feature
---

# Resultado

## Implementado

- `ClassSchedule.rrule` es obligatorio y la única representación operativa de
  recurrencia. Acepta una única línea RFC 5545 `RRULE:...`, sin `DTSTART`.
- La revisión `d3e4f5a6b7c8` convierte el legacy `days_of_week`, verifica que
  el backfill no deje valores nulos y elimina esa columna. Su downgrade es
  deliberadamente forward-only.
- La generación ancla cada regla en `start_date` y `start_time` de `LOCAL_TZ`,
  persiste en UTC y completa solamente ocurrencias futuras faltantes dentro de
  una ventana inclusiva de 15 días.
- No se modifican ni eliminan sesiones, Bookings o `capacity_snapshot`
  existentes. La unicidad `(class_schedule_id, starts_at)` mantiene la
  idempotencia; los solapamientos activos de un mismo profesor se rechazan.

## Validaciones

| Validación | Estado | Evidencia |
|---|---|---|
| Migración en `fitflow_test` | PASS | `c2d3e4f5a6b7 -> d3e4f5a6b7c8`. |
| Metadata y mappers | PASS | Nueve tablas activas y `configure_mappers()` sin error. |
| RRULE / generación / Booking | PASS | Suite completa: 32 passed; generación dirigida (incluye conflicto): 2 passed. |
| OpenAPI | PASS | 70 paths generados en `fitflow-test`. |
| Ruff / Pyright global | FAIL (preexistente) | La base mantiene deuda de lint y tipos fuera del scope RRULE. |

## Pendiente de Review

- Revisar manualmente el cambio de contrato que elimina el endpoint/filtro
  `day_of_week`; las consultas por fecha deben resolver RRULE en una capa
  explícita, no inspeccionar una representación legacy.

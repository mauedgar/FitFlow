---
id: FF-LOCAL-009
status: Done
area: backend
execution_lane: codex
type: feature
---

# Resultado final

## Implementado

- Booking resuelve `class_session_id XOR class_schedule_id` en Service; el
  schedule selecciona la primera sesión futura `scheduled` u `open`.
- La cancelación marca `cancelled_at`, rechaza una segunda cancelación y no
  reescribe reservas con asistencia registrada.
- El CRUD conserva el bloqueo transaccional de cupo/duplicado y rechaza
  sesiones inactivas, soft-deleted o no reservables.
- Client ya no desasocia `User.person_profile`; GymClass se protege con admin y
  Membership se cancela por estado.
- Se añadió auditoría mínima de ClassSchedule y la migración forward-only
  `e4f5a6b7c8d9` con FKs `ON DELETE SET NULL`.

## Validaciones

| Validación | Estado | Evidencia |
|---|---|---|
| `compileall` de app y migraciones | PASS | Sin errores de sintaxis. |
| Pytest unitario dirigido | PASS | 15 passed con Python 3.11.3 temporal y dependencias de test. |
| Pyright dirigido | FAIL (deuda preexistente) | 4 overrides incompatibles en CRUDBase/CRUDBooking/CRUDClassSchedule; ningún diagnóstico nuevo del test o flujo agregado. |
| Docker `fitflow-test` | PASS | PostgreSQL y Redis healthy bajo proyecto `fitflow-test`. |
| Migración en `fitflow_test` | PASS | `d3e4f5a6b7c8 -> e4f5a6b7c8d9`; columnas nullable verificadas. |
| Metadata/mappers/Alembic | PASS | Nueve tablas activas y `alembic check` sin operaciones nuevas. |
| Suite dirigida | PASS | 18 passed: lifecycle, metadata e invariantes de Booking. |

## Riesgos pendientes

- Faltan pruebas HTTP/integración de los flujos incorporados.
- No se verificó contra PostgreSQL el nuevo FK de auditoría.
- No se modificaron cascades ni FK existentes; su política profunda sigue
  cubierta por ADR 0010 y pruebas futuras.

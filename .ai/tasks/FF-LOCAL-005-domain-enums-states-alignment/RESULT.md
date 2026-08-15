---
id: FF-LOCAL-005
title: Auditar y alinear enums y estados del dominio
status: Validation
area: backend
execution_lane: codex
type: refactor
---

# Resultado

## Decisiones implementadas

- `app.core.enums` continúa siendo la única definición activa de enums del dominio. Los valores permanecen en lowercase.
- `ClassSessionStatus` queda confirmado como `scheduled`, `open`, `closed`, `cancelled` y `completed`. `draft` no existe en el contrato activo ni en PostgreSQL.
- `MembershipPlan` y `AllowedPlan` siguen siendo conceptos separados: cobertura contratada y restricción de un `ClassSchedule`, respectivamente.
- Por decisión funcional confirmada, `AllowedPlan.gym_only` se incorpora para que un schedule pueda restringirse a membresías de gimnasio libre.
- La matriz de acceso queda así: `gym_only -> gym_only`; `classes -> classes`; `premium -> gym_only, classes, premium`; `personalized -> gym_only, classes, premium, personalized`.
- `TokenPayload.role` conserva `str | None`, porque representa el payload JWT.
- Los contratos de front desk ya corregidos por el usuario usan `ClassSessionStatus` y `BookingStatus`; no se reescribieron en esta tarea.

## Migración

`c2d3e4f5a6b7_add_gym_only_to_allowedplan.py` agrega el valor `gym_only` al tipo PostgreSQL `allowedplan` con `ADD VALUE IF NOT EXISTS`. Es forward-only: su downgrade se rechaza deliberadamente para evitar una recreación destructiva del enum y sus datos.

## Validaciones

| Validación | Estado | Evidencia |
|---|---|---|
| Inventario de enums y consumidores | PASS | `app.core.enums`, modelos, schemas, services, routers y catálogo de `fitflow_test` inspeccionados. |
| Persistencia previa | PASS | `allowedplan` contenía `classes`, `premium`, `personalized`; el resto de enums coincidía con Python. |
| Reglas de acceso de plan | PASS | Tests unitarios cubren los accesos permitidos y el rechazo de `gym_only -> classes`. |
| Migración de enum en `fitflow_test` | PASS | `allowedplan`: `classes,premium,personalized,gym_only`; revisión Alembic `c2d3e4f5a6b7`. |
| `alembic check` en `fitflow_test` | PASS | No detectó operaciones nuevas. |
| Pytest dirigido | PASS | 22 passed: enum, metadata ORM, invariantes de Booking y smoke. |
| Pyright del test agregado | PASS | 0 errors, 0 warnings. |
| Ruff de imports del test agregado | PASS | `ruff check --select I` sin hallazgos. |
| Ruff completo del alcance | FAIL (preexistente) | La configuración exige shebang en módulos Python y `class_schedule_service.py` conserva imports/noqa ajenos a este cambio; no se amplió el scope a su saneamiento. |

## A revisar / alcance posterior

- Los contratos Pydantic de front desk se revisarán integralmente en FF-LOCAL-006; esta tarea no cambia su diseño.
- RRULE, generación de sesiones y la semántica completa de schedules corresponden a FF-LOCAL-007.

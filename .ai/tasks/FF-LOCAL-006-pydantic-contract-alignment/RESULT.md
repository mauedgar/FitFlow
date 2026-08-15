---
id: FF-LOCAL-006
title: Alinear contratos Pydantic v2 con el dominio consolidado
status: Validation
area: backend
execution_lane: codex
type: refactor
---

# Resultado

## Cambios implementados

- Se incorporó `allowed_plan: AllowedPlan | None` a `ClassScheduleCreate` y
  `ClassScheduleUpdate`, alineando los contratos de entrada con el campo ORM y
  la respuesta pública del schedule. No incorpora RRULE ni reglas de negocio.
- Se preservó `BookingCreate` con validación estructural XOR. La resolución de
  schedule/sesión, capacidad y membresía permanece fuera de Pydantic.
- `FrontDeskSessionView`, `FrontDeskBookingView` y `FrontDeskClassView` usan
  enums runtime de `app.core.enums`, incluidos los cambios previos del usuario.
- `TokenPayload.role` se conserva como `str | None` por ser parte del payload
  JWT, no un contrato de dominio persistente.
- `TeacherWithSchedules` preserva la nulabilidad de `TeacherPublic.schedules`,
  corrigiendo el override incompatible detectado por Pyright.
- Los schemas `Role` y `Permission` permanecen drafts aislados, sin reactivar
  RBAC granular ni eliminar sus contratos futuros.

## Matriz resumida

| Entidad | Create | Update | Public / Internal | Consumidor principal | Estado |
|---|---|---|---|---|---|
| Booking | XOR de schedule/sesión | estado opcional | Public, Internal, vistas | router bookings / service | PASS |
| ClassSchedule | incluye `allowed_plan` | incluye `allowed_plan` | Public e internos | router, CRUD y booking service | PASS |
| ClassSession | Create/Update tipados | estado enum | Public, compactos y relaciones | routers, front desk | PASS |
| GymClass | Create/Update tipados | enums de catálogo | Read/Public | router catálogo | PASS |
| Membership | Create/Update tipados | enums de plan/estado | Public y vistas | router memberships | PASS |
| User / Client / Teacher | contratos separados | updates parciales | Public / vistas | routers de perfil | PASS con deuda de nombres históricos |
| Role / Permission | drafts | drafts | sin endpoint operativo | CRUD legado | LEGACY aislado |

## Validaciones

| Validación | Estado | Evidencia |
|---|---|---|
| Pytest de contratos, enums, metadata y smoke | PASS | 23 passed. |
| XOR de `BookingCreate` | PASS | Casos de uno, ninguno y ambos IDs cubiertos. |
| Serialización JSON de enums y exclusión de campos internos | PASS | Tests unitarios de Front Desk, MembershipPublic y UserPublic. |
| Pyright dirigido | PASS | `test_pydantic_contracts.py` y `class_schedule.py`: 0 errores. |
| Pyright de `app/schemas` | PASS después de corregir `TeacherWithSchedules`; se revalida al cierre. |
| Ruff dirigido por imports | PASS | Test nuevo y schema modificado sin problemas de orden de imports. |
| Ruff de todos los schemas | FAIL preexistente | 46 hallazgos: política `EXE002`, `noqa` obsoletos e imports sin uso preexistentes. No se realiza limpieza masiva en este task. |
| OpenAPI | UNAVAILABLE | Importar `app.main` exige `REDIS_URL`; `fitflow-test` no incluye Redis por diseño. No se modificó infraestructura. |

## A revisar

- Renombrar schemas históricos ambiguos (`Booking`, `ClassSchedule`, `Teacher`,
  etc.) exige auditar consumidores y contratos HTTP; no se hizo un cambio
  incompatible dentro de este task.
- La verificación OpenAPI queda pendiente de un entorno controlado con la
  dependencia Redis de aplicación, sin usar desarrollo.

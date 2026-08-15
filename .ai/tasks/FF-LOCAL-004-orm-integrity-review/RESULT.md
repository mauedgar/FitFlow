# Resultado - SCRUM-32 / TASK-004

**Fecha:** 2026-08-13  
**Estado:** completada para revisión  
**Commit:** no realizado

## Correcciones aplicadas

- `ClassSession` incorpora `SoftDeleteMixin`.
- Se agregó la migración forward-only `b1a2c3d4e5f6` que añade
  `class_sessions.deleted_at TIMESTAMPTZ NULL`.
- Las consultas filtradas de `ClassSession` excluyen también `deleted_at IS NOT
  NULL`; el DELETE existente conserva la semántica de soft delete del CRUD.
- Se agregó un test de integración que confirma que borrar una sesión deja
  `active=false`, fija `deleted_at`, la oculta del CRUD y conserva su Booking.
- `current_bookings_count` se documentó como contador de reservas que consumen
  cupo: excluye `cancelled` tanto en la propiedad Python como en SQL.
- `Booking` no expone DELETE operativo; la cancelación conserva historial.
- La instancia de CRUD de usuarios se normalizó a `user`; los consumidores usan
  un alias local seguro cuando existe una variable `user`.
- `UserRole` se importa desde `app.core.enums`, incluido `schemas/user.py`.
- Booking deja de definir excepciones duplicadas y usa los errores canónicos de
  `app.services.errors`.

## Matriz relacional

| Relación | Estado verificado | Clasificación | Acción |
|---|---|---|---|
| User ↔ Person | `uselist=False` y FK `persons.user_id` sin unique observable | A_REVIEW | No inferir unicidad/cardinalidad de DB; derivar a una decisión de integridad. |
| Person → Client / Teacher | PK compartida hacia `persons.id`; relaciones registradas | CORRECT | Sin cambios. |
| Client ↔ Membership | ORM 1:1, FK sin `ON DELETE`, `delete-orphan` en Client | A_REVIEW | No tocar hasta política de historial de Membership. |
| Client ↔ Booking | 1:N, `ON DELETE CASCADE`, `delete-orphan` | A_REVIEW | Cascade histórico preservado sin cambios. |
| GymClass ↔ ClassSchedule | 1:N, `ON DELETE CASCADE`, `delete-orphan` | A_REVIEW | Cascade histórico preservado sin cambios. |
| ClassSchedule ↔ ClassSession | 1:N, `ON DELETE CASCADE`, `delete-orphan` | A_REVIEW | Cascade histórico preservado sin cambios. |
| ClassSession ↔ Booking | 1:N, `ON DELETE CASCADE`; sesión ahora soft-deletable | CORRECTED | DELETE administrativo conserva Bookings; no se cambiaron FK/cascade. |
| Booking ↔ Client / ClassSession | N:1, ambos pares `back_populates` válidos | CORRECT | Cancelación no elimina la fila. |

Todos los `back_populates` activos resuelven a relaciones existentes y los nueve
modelos activos configuran sus mappers con `lazy="raise"`.

## Alembic y validaciones

- **PASS** — `b1a2c3d4e5f6` aplicado únicamente a `fitflow_test`.
- **PASS** — columna `class_sessions.deleted_at` nullable confirmada y head
  `b1a2c3d4e5f6` confirmado.
- **PASS** — `alembic check`: sin nuevas operaciones de upgrade.
- **PASS** — ORM/smoke e integración: 12 passed.
- **PASS** — metadata y mappers: nueve tablas activas; `deleted_at` presente.
- **FAIL** — Ruff targeted: 15 problemas preexistentes de configuración/estilo
  en archivos alcanzados; no se amplió el scope para reformatearlos.
- **FAIL** — Pyright targeted: tres overrides incompatibles preexistentes en
  `CRUDClassSession.get` y `CRUDUser.get/update`.
- **FAIL** — wrapper completo: Ruff reporta 263 problemas y Pyright 15; los
  hallazgos adicionales son de CRUD, routers, schemas y legado RBAC fuera del
  cambio relacional de esta task.

## Cascades y preservación histórica

No se modificaron cardinalidades, `delete-orphan`, `ON DELETE`, FKs ni índices
preexistentes. Se mantuvieron los riesgos conocidos de baja de Client, Membership,
GymClass y ClassSchedule para una decisión específica de política/ADR.

## Documentación

Se actualizaron `AGENTS.md`, arquitectura, dominio, estado actual, calidad y el
seguimiento ORM con el comportamiento comprobado. No se modificó Jira.

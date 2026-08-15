# Estado actual de FitFlow

**Snapshot documental:** 2026-08-15
**Milestone:** Sprint 6.8 - consolidado en Done
**Objetivo:** preservar un baseline ejecutable y preparar el cierre del MVP.

## Estado general

Sprint 6.8 queda consolidado hasta FF-LOCAL-010. No se conserva el plan
descartado de una matriz HTTP adicional de roles/JWT/Redis.

La arquitectura vigente es `Request -> Schema -> Router -> Service -> CRUD ->
Model -> PostgreSQL`, con FastAPI async, SQLAlchemy 2.x Async, Pydantic v2,
PostgreSQL, JWT y Redis diferido.

## Backend consolidado

- Las entidades activas cargan metadata y mappers SQLAlchemy 2.x.
- Booking resuelve `class_session_id` o `class_schedule_id`, protege capacidad
  y cancela conservando historia.
- Booking cancelado no consume cupo y puede permitir una nueva reserva.
- ClassSession conserva soft delete administrativo; no se borra su historial.
- Client, GymClass y ClassSchedule usan bajas conservativas; Membership cambia
  de estado sin eliminar su historial.
- ClassSchedule registra actor minimo con referencias nullable a User; la
  migracion fue verificada exclusivamente en `fitflow_test`.

## RRULE y sesiones

RRULE es la fuente unica de recurrencia. La generacion usa `LOCAL_TZ`, persiste
sesiones en UTC y completa solo faltantes futuros dentro de 15 dias. No
reescribe sesiones, Bookings ni `capacity_snapshot` existentes. `days_of_week`
no forma parte del contrato activo.

## Front Desk y HTTP

FF-LOCAL-010.1 esta implementada: Front Desk usa un service unico, loaders
explicitos y check-in `confirmed -> attended` con `checked_in_at`.

FF-LOCAL-010.2 esta implementada parcialmente en el alcance consolidado: las
rutas publicas de GymClass, Teacher y ClassSchedule preceden a sus rutas UUID y
la proyeccion publica de GymClass esta completa. La cobertura HTTP integral del
MVP no se declara ejecutada.

La propuesta 010.3 de matriz HTTP completa de roles/JWT/Redis queda descartada.
Redis continua configurado como infraestructura, sin afirmar cobertura de API
que no fue ejecutada.

## Testing y validacion

El baseline vive en `backend/tests/` y usa exclusivamente `fitflow-test` para
pruebas con PostgreSQL. Se validaron metadata, mappers, RRULE, Booking,
cancelacion, capacidad, check-in y Redis en pruebas dirigidas. Pyright de los
modulos tocados por FF-LOCAL-010 fue PASS. La fixture HTTP async compartida y la
suite integral del MVP quedan como deuda explicita.

## Documentacion y workflow

`.ai/tasks/` contiene el contrato y resultado de cada feature flag. FF-LOCAL-009
y FF-LOCAL-010 estan en `Done`. La cobertura HTTP integral del MVP permanece
explicitamente fuera de alcance. `AGENTS.md`, ADRs y documentos de dominio
siguen siendo la guia activa.

No se declara implementado RBAC granular: `Role`, `Permission` y
`role_permissions` permanecen aislados como drafts. `UserRole` es el mecanismo
funcional vigente.

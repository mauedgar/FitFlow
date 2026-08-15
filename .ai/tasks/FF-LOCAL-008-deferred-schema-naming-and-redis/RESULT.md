---
id: FF-LOCAL-008
title: Normalizar contratos Pydantic y configurar Redis
status: Validation
area: backend
execution_lane: codex
type: refactor
---

# Resultado

## Implementado

- Se aplicó el canon `Create`, `Update`, `Public`, `Internal`, `InResponse`,
  `WithRelations` y `Mini` a los contratos afectados. Los nombres ambiguos
  fueron retirados sin aliases: `BookingWithRelations`,
  `ClassScheduleWithRelations`, `TeacherWithRelations`,
  `ClientWithRelations`, `GymClassWithRelations`, `MembershipInternal` y
  `UserInternal`. `ClassSessionWithRelations` sustituye al schema ambiguo.
- `MembershipMini` y `TeacherInScheduleResponseMini` son los `Mini` existentes
  con consumidor real; no se agregaron variantes especulativas.
- Role y Permission siguen como schemas draft aislados, sin reactivar RBAC.
- Compose de desarrollo declara Redis con healthcheck y volumen propio; el
  proyecto `fitflow-test` usa `redis_test` sin puertos ni volumen persistente.
  Ningún archivo `.env` fue cambiado.
- El cliente Redis se crea bajo demanda. Las operaciones de refresh/logout y
  almacenamiento de refresh tokens traducen indisponibilidad a HTTP 503; la
  importación y OpenAPI no abren Redis.

## Validaciones

| Validación | Estado | Evidencia |
|---|---|---|
| Redis aislado | PASS | `redis_test` healthy en `fitflow-test`. |
| Fallo controlado | PASS | Test unitario sin `REDIS_URL` lanza `ExternalServiceError`. |
| OpenAPI | PASS | 70 paths generados sin conectar a Redis. |
| Ruff completo | FAIL (deuda existente) | 200 hallazgos de configuración/estilo en `app` y `tests`; no se amplió este scope a una limpieza global. |
| Pyright completo | FAIL (deuda existente) | 13 errores de overrides CRUD y drafts Role/Permission; no se modificaron para evitar mezclar tareas. |

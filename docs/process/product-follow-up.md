---
document_id: FF-PROCESS-PRODUCT-FOLLOWUP-001
status: review_required
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Seguimiento técnico de producto

Este inventario no autoriza cambios de esquema. Cada ítem requiere confirmación
en el baseline actual antes de convertirse en TASK.

| ID | Estado documental | Próxima verificación |
| --- | --- | --- |
| FF-FOLLOW-02 | review_required | import de app, logout 204 y OpenAPI |
| FF-FOLLOW-05 | partial | bajas Teacher/ClassSchedule y cobertura HTTP |
| FF-FOLLOW-07 | planned | mantener Membership 1:1; evaluar 1:N post-MVP |
| FF-FOLLOW-08 | review_required | defaults/checks/timestamps y drift Alembic |
| FF-FOLLOW-09 | review_required | rebuild desde cero; no reescribir migraciones aplicadas |
| FF-FOLLOW-10 | review_required | obligatoriedad/inicialización de Redis por perfil |
| FF-FOLLOW-11 | review_required | loaders async, `lazy="raise"`, N+1/MissingGreenlet |

Resuelto y no reabrir sin nueva evidencia: baja conservativa de Client,
soft-delete de ClassSession y migración RRULE activa.

La prioridad del producto prevalece sobre mejoras de tooling.

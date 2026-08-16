---
document_id: FF-ADR-0008
status: amended
machine_context: true
amended_by: FF-ADR-0011
---

# ADR 0008: Ciclo de tareas y execution lanes

- **Estado:** Amended por ADR 0011
- **Fecha:** 2026-08-13
- **Enmienda:** 2026-08-16

## Contexto

FitFlow necesita un contrato común entre personas, agentes, Git y el sistema de
seguimiento.

## Decisión que permanece

- Jira o el tracker controla prioridad y estado de negocio.
- `TASK.md` define el contrato técnico.
- `PLAN.md` conserva la estrategia cuando sea necesaria.
- `STATUS.md` registra progreso durable.
- `RESULT.md` normaliza el cierre técnico.
- Git conserva implementación y diff.
- `docs/` recibe solo conocimiento durable aceptado.

## Enmienda

Las execution lanes por producto/agente se reemplazan por `human`,
`ai_orchestrated` y `mixed`. El rol concreto y el modelo se registran por
ejecución, no como lane de Jira.

La máquina de estados detallada y los límites de autonomía se definen en ADR
0011 y `docs/process/task-lifecycle-and-reporting.md`.

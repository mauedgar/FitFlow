---
document_id: FF-ADR-0008
status: amended
machine_context: true
amended_by: [FF-ADR-0014, FF-ADR-0016]
---

# ADR 0008: Ciclo de tareas y execution lanes

- **Estado:** Amended por ADR 0014 y ADR 0016
- **Fecha:** 2026-08-13
- **Enmienda:** 2026-08-18

## Contexto

FitFlow necesita un contrato comun entre desarrolladores, agentes, Git y el sistema de
seguimiento.

## Decisión que permanece

- GitHub Project controla prioridad y macroestado operativo.
- GitHub Issue es TASK principal cuando esta sincronizada.
- `TASK.md` define el contrato técnico.
- `PLAN.md` conserva la estrategia cuando sea necesaria.
- `STATUS.md` registra progreso durable.
- `RESULT.md` normaliza el cierre técnico.
- Git conserva implementación y diff.
- `docs/` recibe solo conocimiento durable aceptado.

## Enmienda

Las execution lanes v2 son `developer`, `ai_orchestrated`, `mixed` y
`undecided`. `human` queda como valor historico v1. El rol y el modelo se
registran por ejecucion, no como lane del Project.

La máquina de estados detallada y los límites de autonomía se definen en ADR
0014, 0016 y `docs/process/task-lifecycle-and-reporting.md`.

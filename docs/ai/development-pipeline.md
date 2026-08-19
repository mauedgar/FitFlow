---
document_id: FF-AI-PIPELINE-DEV-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Pipeline de desarrollo asistido

## State Machine

`BACKLOG -> READY -> PLANNING -> ROUTING -> EXPLORING -> EXECUTING -> VALIDATING -> REVIEWING -> DOC_SYNC -> PENDING_ACCEPTANCE -> DONE`

`WAITING_DEVELOPER`, `BLOCKED`, `BLOCKED_HIGH_RISK` y `CANCELLED` son estados
laterales. `DONE` solo acepta actor `developer`.

## Etapas

| Estado | Responsable | Salida |
| --- | --- | --- |
| `PLANNING` | Developer Planner | TASK/PLAN aprobados |
| `ROUTING` | Router + Model Resolver | RouteDecision |
| `EXPLORING` | Explorer | ContextRequest/ContextPackageResult |
| `EXECUTING` | Coder seleccionado | ExecutionResult |
| `VALIDATING` | Validator | ValidationResult |
| `REVIEWING` | Reviewer | ReviewResult |
| `DOC_SYNC` | Doc Curator | DocImpact y patch propuesto |
| `PENDING_ACCEPTANCE` | workflow | Result consolidado |

## Rutas de fallo

| Condicion | Siguiente estado |
| --- | --- |
| contexto insuficiente o stale | `EXPLORING` |
| implementacion/validacion fallida | `ROUTING` |
| review `FAIL` localizado | `ROUTING` |
| review `REPLAN` | `PLANNING` |
| decision o scope ambiguo | `WAITING_DEVELOPER` |
| riesgo alto | `BLOCKED_HIGH_RISK` |
| dependencia ausente | `BLOCKED` con `UNAVAILABLE` |

Los limites se leen de policy. Agotar retries produce un resultado parcial y
escala; nunca habilita un loop autonomo.

## Workflows MVP

- `development`: plan, route, explore, execute, validate, review, docs, approve.
- `bugfix`: plan, route, explore/reproduce, fix, validate, review, docs, approve.
- `documentation_sync`: diff/result, doc impact, curate, review, approve.

Orchestrator-workers, optimizer autonomo y Temporal permanecen deshabilitados.

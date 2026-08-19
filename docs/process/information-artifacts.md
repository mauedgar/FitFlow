---
document_id: FF-PROCESS-ARTIFACTS-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Artefactos y trazabilidad

## Regla comun

Los artefactos v2 incluyen `artifact`, `schema_version`, `task_id`, `run_id`,
timestamp, actor y baseline cuando aplica. Usan `.ai/contracts/v2/`, rutas
relativas y enums cerrados. Valores desconocidos son `null`; no se inventan.

## Matriz

| Artefacto | Produce | Consume | Proposito |
| --- | --- | --- | --- |
| Task | Developer Planner | workflow/roles | objetivo, scope, risk, ownership y AC |
| RouteDecision | Router | Explorer/Model Resolver | rol, capability, estrategia y motivo |
| ContextRequest | Explorer | ContextPackager | necesidad explicita, modo y budget |
| ContextPackageResult | ContextPackager | Explorer/rol | evidencia, omissions, freshness y hash |
| ExecutionResult | Coder | Validator | archivos, self-check y riesgos |
| ValidationResult | Validator | Reviewer/workflow | comandos, salidas y estado normalizado |
| ReviewResult | Reviewer | Router/workflow | findings, veredicto y next state |
| DocImpact | Doc Curator | Developer Planner | conocimiento durable y patch propuesto |
| RunEvent/RunState | workflow | todos | transiciones, retries, lineage y bloqueo |
| UsageRecord/FinOpsSummary | runtime/policy | observer/developer | recursos, tokens, quota, costo y eficiencia |
| RunResult | workflow | desarrollador | consolidacion para PENDING_ACCEPTANCE |

## Serializacion

JSON es el contrato neutral y durable. Markdown TASK/PLAN/REVIEW/VALIDATION/
RESULT es una vista para desarrolladores. XML historico puede orientar contexto,
pero no es contrato obligatorio de AI Core vNext.

## Inmutabilidad

Un artefacto aceptado no se reescribe para ocultar un fallo. Se agrega un nuevo
evento, amendment o run con referencia al anterior.

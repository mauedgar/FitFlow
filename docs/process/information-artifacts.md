---
document_id: FF-PROCESS-ARTIFACTS-001
status: canonical
machine_context: true
version: 2.1
updated: 2026-08-25
---

# Artefactos y trazabilidad

## Alcance contractual

Este documento gobierna los artefactos operativos que FitFlow conserva como
consumidor del AI Core. No gobierna los schemas Pydantic/OpenAPI del producto ni
la implementacion interna de FitFlow-ai.

FitFlow-ai define los contratos Zod ejecutables y el runtime generico. FitFlow
conserva el Project Profile, TASK, runs y evidencia especificos, y los valida
con el snapshot JSON Schema v2 del baseline declarado. La sincronizacion de
ambas representaciones permanece `MIGRATION_PENDING`; ninguna divergencia se
armoniza unilateralmente en este repositorio.

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

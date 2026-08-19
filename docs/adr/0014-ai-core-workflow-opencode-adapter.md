---
document_id: FF-ADR-0014
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-18
supersedes: [FF-ADR-0011]
amends: [FF-ADR-0008]
---

# ADR 0014: AI Core, Workflow-as-Code y adapter OpenCode

## Contexto

La baseline v4 entregaba la autoridad operativa a una superficie concreta y
mezclaba orquestacion con ejecucion de roles. El paradigma vNext requiere
workflow testeable y adapters reemplazables.

## Decision

Adoptar AI Core reutilizable con functional core/imperative shell y State
Machine TypeScript. OpenCode implementa `AgentRuntimePort`; no gobierna estados,
retries, risk gates ni persistencia.

El desarrollador es Planner activo y autoridad de `DONE`. PlannerAI permanece
disabled. Router aplica reglas deterministas y fallback LLM; Model Resolver se
mantiene separado. Validator precede a Reviewer y un FAIL vuelve a Router.

## Consecuencias

El adapter OpenCode requiere discovery y conformance tests. OpenCode puede
reemplazarse sin cambiar contratos del workflow. No se instala ni implementa el
runtime como parte de esta decision documental.

---
document_id: FF-AI-ROLES-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Roles y routing de modelos

## Roles

| Rol | Estado vNext | Responsabilidad |
| --- | --- | --- |
| Developer Planner | active | objetivo, plan, riesgo, decisiones y aceptacion |
| PlannerAI | disabled | futura asistencia de planificacion |
| Router | active specification | seleccionar rol/capacidad o escalar |
| Model Resolver | active specification | seleccionar pool/modelo elegible |
| Explorer | active specification | decidir evidencia minima necesaria |
| CoderB | active specification | cambio mecanico y reversible |
| CoderA | active specification | implementacion acotada media |
| CoderStrongA | conditional specification | escalamiento complejo permitido |
| Reviewer | active specification | findings y veredicto independiente |
| Architect | conditional specification | decision arquitectonica autorizada |
| Doc Curator | active specification | proponer sincronizacion durable |
| Validator | active specification, non-agentic | ejecutar comandos y normalizar estados |

Security Reviewer, Performance Reviewer, Migration Engineer,
Orchestrator-workers y optimizers autonomos se registran disabled.

`active specification` describe el contrato objetivo aceptable para
implementacion; no afirma que el componente runtime exista. Solo Developer
Planner esta activo como autoridad operativa en esta baseline propuesta.

## Router

1. Aplicar reglas por riesgo, scope, task type, ownership y retry history.
2. Si la salida es unica, emitir `RouteDecision` sin LLM.
3. Si hay ambiguedad permitida, usar fallback LLM economico.
4. Si la confianza no alcanza el threshold, escalar al desarrollador.
5. Router selecciona rol/capacidad; no selecciona un modelo fijo.

## Model Resolver

Filtra Model Registry por capabilities, trust, availability, quota pool,
criticality ceiling, contexto, benchmark y provider policy. Elige el recurso
suficiente de menor costo total esperado. Registra pool, runtime ID efectivo,
fallback y motivo.

Clases de recurso: `deterministic`, `local`, `included`, `free_external`,
`paid`. `paid` esta disabled. GitHub Copilot esta deferred y solo admite
intermediacion manual del desarrollador, por lo que no es elegible para routing.
Calidad y riesgo preceden al costo.

## Explorer

Explorer es un rol, no una tool. FastContext es un candidato de modelo local,
no una dependencia exclusiva. El rol puede usar `repo-packager`, `rg`, LSP y,
posteriormente, retrieval semantico. La promocion de un modelo requiere evals
por `role + task_type + risk`.

## Independencia

Reviewer no usa la misma ejecucion efectiva del Coder cuando existe una
alternativa elegible. Ningun modelo experimental o runtime desconocido puede
aprobar arquitectura, seguridad, migraciones o documentacion canonica.

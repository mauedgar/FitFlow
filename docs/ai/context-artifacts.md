---
document_id: FF-AI-ARTIFACTS-001
status: canonical
machine_context: true
version: 2.1
updated: 2026-08-26
ownership_classification: MIGRATION_PENDING
---

# Artefactos vNext

## Contratos estables

`Task`, `RouteDecision`, `ContextRequest`, `ContextPackageResult`,
`ExecutionResult`, `ValidationResult`, `ReviewResult`, `DocImpact`, `RunEvent`,
`RunState`, `UsageRecord` y `FinOpsSummary` se validan con
`.ai/contracts/v2/`.

Estos JSON Schema son contratos consumidores del intercambio operativo con
FitFlow-ai. No son schemas Pydantic del producto, no describen endpoints web y
no implementan la maquina de estados. FitFlow-ai conserva la autoridad sobre
los contratos Zod y el runtime generico; FitFlow conserva los TASK, runs,
evidencia y Project Profile especificos que los schemas locales validan.

## Estado de sincronizacion

La distribucion versionada del contrato productor permanece
`MIGRATION_PENDING`: npm, submodulo u otro mecanismo no han sido adoptados como
canonicamente operativos. Los schemas v2 locales representan el baseline
consumidor vigente y no se modifican de forma unilateral.

Un cambio contractual requiere:

1. version nueva o decision explicita en FitFlow-ai;
2. clasificacion de compatibilidad para el consumidor;
3. validacion de los artefactos de FitFlow afectados;
4. actualizacion explicita del baseline y de esta documentacion.

Las divergencias conocidas, incluido el vocabulario de `ReviewResult`, no se
resuelven por aliases o inferencia local. Bloquean solo el cambio contractual
afectado, no el lifecycle de desarrollo del producto.

## Persistencia

```text
.ai/runs/<run_id>/
  run-state.json
  events.jsonl
  route.json
  context-*.json
  execution.json
  validation.json
  review.json
  doc-impact.json
  usage.jsonl
  result.json
```

Solo se crean artefactos aplicables. Los JSON aceptados son evidencia durable.
`.ai/local/run-state.sqlite` conserva checkpoints y consultas locales; puede
reconstruirse desde eventos y no se versiona.

## GitHub

PR comments y checks muestran un resumen consolidado. Actions artifacts pueden
transportar evidencia temporal. Ninguno reemplaza el artefacto local canonical.

## Lineage

Los artefactos principales declaran schema version, task/run, baseline y
timestamp cuando aplica. `RunEvent` registra el productor mediante `actor` y
enlaza inputs/outputs con referencias hash. Cada evidencia de codigo agrega
path, hash y, cuando aplica, rango/simbolo. Un artifact stale no habilita
transicion.

## Markdown

TASK/PLAN/REVIEW/VALIDATION/RESULT Markdown son vistas para el desarrollador.
No constituyen un contrato alternativo cuando existe JSON v2 del mismo run.

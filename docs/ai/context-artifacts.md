---
document_id: FF-AI-ARTIFACTS-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Artefactos vNext

## Contratos estables

`Task`, `RouteDecision`, `ContextRequest`, `ContextPackageResult`,
`ExecutionResult`, `ValidationResult`, `ReviewResult`, `DocImpact`, `RunEvent`,
`RunState`, `UsageRecord` y `FinOpsSummary` se validan con
`.ai/contracts/v2/`.

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

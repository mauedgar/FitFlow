---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-010
title: Instrumentar Phoenix y correlación de runs
status: BACKLOG
task_type: tooling
scope: docs_tooling
lane: ai_orchestrated
risk: medium
priority: P1
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-003, FF-AI-005]
ownership_keys:
  - path:FitFlow-ai/src/observability
  - config:phoenix-v1
required_docs:
  - docs/ai/observability-and-evaluation.md
  - docs/adr/0013-phoenix-observability.md
---

# Objetivo

Emitir trazas Phoenix/OpenTelemetry correlacionadas sin filtrar secretos ni
inflar almacenamiento.

## Scope

- spans de pipeline de desarrollo e indexación;
- task/run/stage/role/model/revisión/índice;
- tokens, latencia y estado cuando estén disponibles;
- allowlist, redacción y retención.

## Fuera de scope

- telemetría de producción de FitFlow o contenido completo por defecto.

## Criterios de aceptación

1. Un piloto se reconstruye por task/run de inicio a aceptación.
2. Fallback de modelo queda visible.
3. Secret scanner de atributos no encuentra credenciales/`.env`.
4. La ausencia de Phoenix no altera la corrección del pipeline; queda
   `UNAVAILABLE` y se conserva log local mínimo.
5. Retención/export definidos y aprobados.

## Validación esperada

Collector local, spans de fixture, redaction tests y fallo de backend.

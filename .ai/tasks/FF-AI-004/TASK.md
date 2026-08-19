---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-004
title: Evaluar recuperación y presupuesto de contexto
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-011
task_type: test
scope: mixed
lane: mixed
risk: low
priority: P0
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-003]
ownership_keys:
  - path:FitFlow-ai/tests/evals/retrieval
  - doc:FF-AI-CONTEXT-METRICS
required_docs:
  - docs/ai/context-strategy.md
  - docs/ai/observability-and-evaluation.md
---

# Objetivo

Medir si el sistema recupera evidencia útil dentro de presupuestos conservadores.

## Scope

- 15–20 consultas doradas backend/frontend/mixed;
- expected paths/symbols, evidencia prohibida y top-k;
- recall útil, precisión, citas, staleness, latencia y tokens;
- comparación textual/estructural/vectorial/combinada.

## Fuera de scope

- alterar autonomía por una única corrida o usar solo evaluación subjetiva.

## Criterios de aceptación

1. Fixtures versionados y repetibles.
2. Baseline por estrategia y modelo.
3. Fallos explicados por categoría, sin tunear contra datos ocultos.
4. Recomendación explícita de parámetros y gaps.
5. Presupuestos 8k/8k/12k no aumentan sin aprobación.

## Validación esperada

Reporte machine-readable y Markdown, ejecución repetida y verificación manual de
una muestra de citas.

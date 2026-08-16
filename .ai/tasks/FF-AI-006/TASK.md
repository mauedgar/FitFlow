---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-006
title: Implementar evaluación de prompts y modelos
status: BACKLOG
task_type: test
scope: docs_tooling
lane: ai_orchestrated
risk: low
priority: P1
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-004, FF-AI-005]
ownership_keys:
  - path:FitFlow-ai/tests/evals/agents
  - config:promptfoo-v1
required_docs:
  - docs/ai/observability-and-evaluation.md
  - docs/ai/roles-and-model-routing.md
---

# Objetivo

Comparar prompts/modelos/fallbacks por rol usando Promptfoo y checks
deterministas.

## Scope

- fixtures por rol/tipo/riesgo;
- validación de schema, evidencia esperada y prohibiciones;
- métricas de pass, costo/latencia y retrabajo;
- resultados por modelo efectivo.

## Fuera de scope

- juez LLM único, promoción global o high risk.

## Criterios de aceptación

1. Casos positivos y adversariales por rol.
2. Outputs no serializables fallan.
3. Coder B falla correctamente ante una tarea fuera de alcance.
4. Recomendación de routing basada en resultados reproducibles.
5. Secretos/contenido sensible no aparecen en reportes.

## Validación esperada

Suite Promptfoo fijada, reporte JSON/HTML ignorado y resumen versionable.

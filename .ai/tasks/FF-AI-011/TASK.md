---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-011
title: Afinar matriz de modelos por métricas
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-007
task_type: audit
scope: docs_tooling
lane: mixed
risk: low
priority: P2
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-006, FF-AI-008, FF-AI-010]
ownership_keys:
  - config:model-routing-v2
  - doc:FF-AI-ROLES-001
required_docs:
  - docs/ai/roles-and-model-routing.md
  - docs/ai/observability-and-evaluation.md
---

# Objetivo

Promover/degradar candidatos GPT, Grok, Copilot y locales por rol con evidencia
de calidad, retrabajo, latencia y costo.

## Scope

- resultados por role/task_type/risk;
- Qwen 7B/3B, DeepSeek R1 8B y FastContext en los usos permitidos;
- fallbacks y criterios de promoción;
- actualización versionada de routing.

## Fuera de scope

- promoción global, tareas high risk o elegir por preferencia sin benchmark.

## Criterios de aceptación

1. Cada cambio de route referencia fixtures y runs.
2. Reviewer mantiene independencia.
3. Coder B conserva alcance literal.
4. Ningún modelo local pequeño decide arquitectura.
5. Decisión humana acepta o rechaza la matriz v2.

## Validación esperada

Re-run del golden set y comparación con baseline v1.

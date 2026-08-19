---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-005
title: Implementar orquestación Codebase v1
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-008
task_type: tooling
scope: docs_tooling
lane: mixed
risk: medium
priority: P0
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-004]
ownership_keys:
  - path:FitFlow-ai/src/adapters/codebase
  - config:orchestrator-v1
  - path:FitFlow/.ai/prompts
required_docs:
  - docs/ai/codebase-operating-guide.md
  - docs/ai/development-pipeline.md
  - docs/ai/roles-and-model-routing.md
---

# Objetivo

Traducir contratos neutrales a la configuración real de Codebase y ejecutar la
máquina de estados con roles separados.

## Scope

- adapter validado para config/prompts/tools/model IDs;
- estados/transiciones/reintentos y outputs contra schema;
- bloqueo high risk, ownership y terminal humano;
- backend/frontend/mixed;
- logging de provider/model/fallback.

## Fuera de scope

- MCP, commits automáticos, despliegues o riesgo alto.

## Criterios de aceptación

1. Fixture de cada transición válida e inválida.
2. No asigna Coder a high risk.
3. Reviewer es ejecución independiente.
4. Un output inválido bloquea transición.
5. El flujo finaliza en `PENDING_ACCEPTANCE`.

## Validación esperada

Dry runs sin cambios, sandbox de fixtures local si existe, y piloto de docs
low-risk antes de código.

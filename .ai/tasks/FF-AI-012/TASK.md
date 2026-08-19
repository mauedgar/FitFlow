---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-012
title: Implementar locks de ownership y paralelismo seguro
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-004
task_type: tooling
scope: mixed
lane: ai_orchestrated
risk: medium
priority: P2
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-005, FF-AI-008]
ownership_keys:
  - path:FitFlow-ai/src/orchestration/locks
  - config:ownership-locks-v1
required_docs:
  - docs/process/risk-and-parallelism.md
  - .ai/contracts/ownership-lock.schema.json
---

# Objetivo

Permitir paralelismo únicamente cuando paths y responsabilidades no se cruzan.

## Scope

- resolución de ownership keys a recursos explícitos;
- locks read/write, expiración verificada y liberación;
- detección de dependencia de contrato no aceptado;
- integración con dispatch y trazas.

## Fuera de scope

- auto-merge, resolución automática de conflictos o robo ciego de locks.

## Criterios de aceptación

1. Writer/writer y writer/reader solapados se bloquean.
2. Reader/reader disjunto o compartido se permite.
3. Backend/frontend con contrato no aceptado se serializa.
4. Expiración exige verificación del run anterior.
5. Fixtures de race no producen dos writers activos sobre una key.

## Validación esperada

Unit de intersección, integration concurrente y replay de crashes.

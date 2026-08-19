---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-007
title: Exponer contexto mediante MCP read-only
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-012
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
depends_on: [FF-AI-004, FF-AI-005]
ownership_keys:
  - path:FitFlow-ai/src/mcp
  - config:mcp-read-only-v1
required_docs:
  - docs/ai/mcp-policy.md
  - docs/ai/context-strategy.md
---

# Objetivo

Exponer consultas acotadas del índice a Codebase sin capacidades de escritura.

## Scope

- context query, symbol lookup, related files, index status y lectura de ficha;
- allowlists, scopes, baseline, presupuesto y trazas;
- schemas de request/response y timeouts.

## Fuera de scope

- shell, Git, edición, index promote, secretos o transición de tareas.

## Criterios de aceptación

1. Cada tool rechaza task/scope/baseline inválidos.
2. Ninguna tool escribe fuera de logs/telemetría permitida.
3. Rutas excluidas y archive nunca aparecen.
4. Respuestas citan evidencia y respetan límites.
5. Threat model y pruebas adversariales aprobadas por una persona.

## Validación esperada

Contract tests, traversal/secret tests, timeout/payload limits y auditoría de
permisos.

---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-008
title: Ejecutar piloto end-to-end low y medium
status: BACKLOG
task_type: test
scope: mixed
lane: mixed
risk: medium
priority: P1
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-005, FF-AI-006]
ownership_keys:
  - path:FitFlow-ai/tests/e2e/pilot
  - doc:FF-AI-PILOT-RESULT
required_docs:
  - docs/ai/development-pipeline.md
  - docs/process/risk-and-parallelism.md
---

# Objetivo

Probar el ciclo completo con tareas reales no críticas antes de ampliar uso.

## Scope

- al menos una tarea docs low, backend low, frontend low y medium acotada;
- plan, contexto, coder, review, validación y aceptación humana;
- medición de reintentos, scope, tokens, latencia y fallos.

## Fuera de scope

- auth, migraciones, transacciones críticas, despliegue o commits por agente.

## Criterios de aceptación

1. Todos los artefactos validan y conservan correlación.
2. Ningún run salta estados ni finaliza DONE automáticamente.
3. Contexto stale bloquea edición en fixture adversarial.
4. Hallazgos se convierten en follow-ups, no ajustes ocultos.
5. Persona decide continuar, limitar o pausar el sistema.

## Validación esperada

Replay de runs, diff review y reporte consolidado por tipo/riesgo/modelo.

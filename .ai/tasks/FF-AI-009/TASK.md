---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-009
title: Automatizar sincronización incremental por módulos
status: CANCELLED
# vNext: SUPERSEDED_BY FF-AI-VNEXT-004
task_type: tooling
scope: mixed
lane: ai_orchestrated
risk: medium
priority: P1
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-003, FF-AI-008]
ownership_keys:
  - path:FitFlow-ai/src/hooks/indexing
  - config:index-triggers-v1
required_docs:
  - docs/ai/indexing-pipeline.md
  - docs/ai/cli-contract.md
---

# Objetivo

Conectar create/change/delete de módulos con dirty manifests, sync post-gates y
promoción humana.

## Scope

- hooks idempotentes `mark_dirty`, `sync`, `verify`, `promote`;
- correlación task/run/baseline;
- debouncing y locks;
- recuperación ante interrupción;
- deletes/renames.

## Fuera de scope

- reindexar cada save, promover antes de aceptación o modificar producto desde
  el hook.

## Criterios de aceptación

1. Diez saves del mismo path producen una unidad dirty deduplicada.
2. Sync solo corre tras gates configurados.
3. Fallo no pierde manifest y no promueve parcialmente.
4. Delete/rename no deja chunks huérfanos.
5. Rebuild se dispara al cambiar parser/chunker/embedding/exclusions.

## Validación esperada

Fixtures de secuencia, concurrencia de hooks, crash/retry y comparación full vs
incremental.

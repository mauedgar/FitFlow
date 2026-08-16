---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-003
title: Implementar ingesta LlamaIndex, EmbeddingGemma y Qdrant
status: BACKLOG
task_type: tooling
scope: mixed
lane: ai_orchestrated
risk: medium
priority: P0
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: [FF-AI-000, FF-AI-001, FF-AI-002]
ownership_keys:
  - path:FitFlow-ai/src/ingestion
  - path:FitFlow-ai/src/retrieval
  - config:qdrant-collection-v1
required_docs:
  - docs/ai/indexing-pipeline.md
  - docs/ai/context-strategy.md
---

# Objetivo

Crear un pipeline incremental que ingeste contexto permitido, genere embeddings
con EmbeddingGemma-300M y sincronice Qdrant con upserts y deletes.

## Scope

- loaders, metadata, chunking estructural/fallback y IDs v1;
- docstore/hash strategy y borrados;
- colección Qdrant versionada con filtros;
- build/sync/verify/promote;
- índice de trabajo separado del promovido.

## Fuera de scope

- cambio de embedding, MCP, dispatch de agentes o reindexar cada save.

## Criterios de aceptación

1. Build limpio y sync incremental producen el mismo conjunto lógico.
2. Modificación hace upsert y borrado elimina nodos sin residuos.
3. Solo docs `machine_context: true` ingresan.
4. Toda query filtra repo/scope/revisión y devuelve citas.
5. Fallo parcial no promueve índice.

## Validación esperada

Qdrant de test, fixtures create/update/delete, conteos, hashes, smoke queries y
rebuild por cambio de modelo/config.

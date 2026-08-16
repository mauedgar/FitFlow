---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-001
title: Implementar fuentes de contexto estructural v1
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
depends_on: [FF-AI-000]
ownership_keys:
  - path:FitFlow-ai/scripts/structure
  - config:context-exclusions
required_docs:
  - docs/ai/context-artifacts.md
  - docs/ai/cli-contract.md
  - docs/process/ignore-policy.md
---

# Objetivo

Generar inventarios backend/frontend/total, XML estructural inicial y bundles
Repomix reproducibles para cada scope.

## Scope

- CLI Node para discovery/exclusions y perfiles Repomix.
- nombres exactos de inventarios y `estructura_de_clases_<fecha>.xml`.
- manifest con baseline/fingerprint, versiones, hashes y conteos.
- XML validado contra XSD; backend/frontend/mixed.

## Fuera de scope

- Embeddings semánticos (EmbeddingGemma), Qdrant o MCP.

## Criterios de aceptación

1. Los tres inventarios son deterministas y no contienen paths excluidos.
2. El XML total valida y marca relaciones inferidas/confidence.
3. Repomix usa el mismo perfil de exclusión y scope.
4. Dos ejecuciones sin cambios producen hashes iguales salvo metadata temporal
   separada del contenido estable.
5. Tests cubren exclusiones, secrets, paths con espacios y borrados.

## Validación esperada

Fixtures mínimos backend/frontend, validación XSD, snapshot diff y prueba de no
inclusión de `.env`, entornos y archive.

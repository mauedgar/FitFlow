---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-002
title: Implementar índice estructural con Repomix/repo-packager
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
depends_on: [FF-AI-000, FF-AI-001]
ownership_keys:
  - path:FitFlow-ai/src/structure
   - config:repomix-profiles
   - note: Tree-sitter reemplazado por Repomix/repo-packager; fallback a xml_generator
required_docs:
  - docs/ai/indexing-pipeline.md
  - docs/ai/context-artifacts.md
---

# Objetivo

Extraer símbolos, imports y relaciones de Python/TypeScript con IDs
deterministas, sustituyendo el generador estructural provisional.

## Scope

- parsers/grammars fijados tras FF-AI-000;
- clases, funciones, métodos, imports, calls/extends cuando sean confiables;
- parse status y errores por archivo;
- salida XML compatible y manifest incremental;
- fixtures FitFlow representativos.

## Fuera de scope

- inferencia arquitectónica por LLM o vectorización.

## Criterios de aceptación

1. Mismo input/config produce mismos IDs/relaciones.
2. Rangos son 1-based y verificables en archivo.
3. Sintaxis no soportada queda `PARTIAL|UNPARSED`, no desaparece.
4. Create/change/delete actualiza solo paths afectados.
5. XML valida y supera fixtures Python/TS definidos.

## Validación esperada

Unit de queries, golden XML, incremental/rename/delete y benchmark de tiempo.

---
artifact: TASK
schema_version: fitflow-task/v1
task_id: FF-AI-000
title: Auditar compatibilidad del entorno de tooling
status: READY
task_type: audit
scope: docs_tooling
lane: mixed
risk: low
priority: P0
created_at: "2026-08-16T00:00:00-03:00"
baseline_revision: TO_BE_CAPTURED_AT_START
working_tree_fingerprint: "sha256:TO_BE_CAPTURED_AT_START"
author_role: human
run_id: NOT_STARTED
depends_on: []
ownership_keys:
  - config:env_tools
  - doc:FF-AI-COMPATIBILITY
required_docs:
  - docs/ai/indexing-pipeline.md
  - docs/quality-and-validation.md
---

# Objetivo

Producir una matriz reproducible de versiones y restricciones antes de instalar
o actualizar cualquier dependencia.

## Scope

- Python efectivo de `env_tools` y backend.
- pytest, pytest-asyncio, Ruff, Pyright y presencia/uso real de Pylint.
- Repomix profiles/configs, networkx (para PageRank), LlamaIndex, cliente Qdrant, embedding runtime,
  Repomix y Node/npm.
- Import smoke y resolución de dependencias.

## Fuera de scope

- upgrades, downgrades, reinstalaciones o edición de lockfiles.
- incorporar Pylint como gate.

## Criterios de aceptación

1. Matriz con versión instalada, requisito, compatibilidad observada y evidencia.
2. Comandos exactos y outputs resumidos.
3. Conflictos clasificados como bloqueantes/no bloqueantes.
4. Si hace falta cambio, propuesta separada con impacto y rollback.
5. Estado final `PASS`, `FAIL` o `UNAVAILABLE`; nunca compatibilidad inferida.

## Validación esperada

Imports y comandos `--version` read-only; resolver dependencia sin modificar el
entorno cuando la herramienta lo permita.

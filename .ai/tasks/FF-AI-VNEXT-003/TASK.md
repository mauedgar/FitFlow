---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-AI-VNEXT-003
title: Implementar contracts y registries v2
status: DONE
task_type: tooling
area: ai_tooling
scope: docs_tooling
lane: ai_orchestrated
risk: low
priority: P0
created_at: "2026-08-18T16:30:00-03:00"
author_role: developer
baseline:
  revision: 44952257482192c438cb38f80be623056fce2409
  fingerprint_status: unavailable
  working_tree_fingerprint: null
  fingerprint_reason: "El arbol contiene cambios de la migracion vNext en curso; no se capturo un fingerprint antes de la tarea."
github_issue: null
openspec_change: null
ownership_keys:
  - "path:../FitFlow-ai/src/contracts"
  - "path:../FitFlow-ai/src/registries"
required_docs:
  - docs/ai/fitflow-ai-layout.md
  - docs/ai/ai-core-architecture.md
  - docs/ai/roadmap-vnext.md
---

# Objetivo

Implementar contracts v2 como schemas Zod en AI Core y registries loaders que
cargan y validan la configuracion real de `../.ai/config/*.yaml` sin duplicar
valores en codigo.

## Scope

- `../FitFlow-ai/src/contracts/` (Zod: common, task, run-event, run-state, validation);
- `../FitFlow-ai/src/registries/` (loader YAML + schemas orchestrator, roles, models, project-profile, finops);
- tests en `../FitFlow-ai/tests/contract/`.

## Fuera de scope

- State Machine ni Run Store (FF-AI-VNEXT-004);
- instalacion de dependencias no autorizadas.

## Restricciones

- zod en core, JSON Schema en bordes;
- registries como datos versionados; AI Core no duplica sus valores;
- dependencias autorizadas: `zod@4` y `yaml@2` en `FitFlow-ai`.

## Criterios de aceptacion

| ID | Criterio | Evidencia esperada |
| --- | --- | --- |
| AC-1 | contracts v2 validan con zod | tests contract PASS |
| AC-2 | registries loaders cargan configuracion real | tests registry PASS |
| AC-3 | DONE solo emitible por developer desde PENDING_ACCEPTANCE | guard zod negativo |
| AC-4 | dependencias declaradas en ../FitFlow-ai/package.json | zod y yaml instalados |

## Impacto documental

`canonical_update` y actualizacion de `docs/ai/cli-contract.md`.

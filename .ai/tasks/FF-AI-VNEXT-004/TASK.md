---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-AI-VNEXT-004
title: Implementar State Machine y Run Store
status: READY
task_type: tooling
area: ai_tooling
scope: docs_tooling
lane: ai_orchestrated
risk: medium
priority: P0
created_at: "2026-08-18T17:45:00-03:00"
author_role: developer
baseline:
  revision: 44952257482192c438cb38f80be623056fce2409
  fingerprint_status: unavailable
  working_tree_fingerprint: null
  fingerprint_reason: "El arbol contiene cambios de la migracion vNext en curso; no se capturo un fingerprint antes de la tarea."
github_issue: null
openspec_change: null
ownership_keys:
  - "path:../FitFlow-ai/src/core"
  - "path:../FitFlow-ai/tests/core"
required_docs:
  - docs/ai/fitflow-ai-layout.md
  - docs/ai/ai-core-architecture.md
  - docs/ai/roadmap-vnext.md
---

# Objetivo

Implementar el nucleo del AI Core: una State Machine determinista gobernada por
las transiciones del `orchestrator.yaml` real y un Run Store durable
(filesystem JSON en `.ai/runs`) con proyeccion local SQLite en `.ai/local`.

## Scope

- `../FitFlow-ai/src/core/state-machine.js` (transiciones del orchestrator, DONE
  solo por developer desde `PENDING_ACCEPTANCE`);
- `../FitFlow-ai/src/core/run-store.js` (events JSONL + run-state JSON + proyeccion
  SQLite con `better-sqlite3`);
- tests en `../FitFlow-ai/tests/core/`.

## Fuera de scope

- Router, Model Resolver, Explorer, Validator, Reviewer (fases D/E);
- adapters de contexto (context-packager pausado);
- promocion a `DONE` (autoridad del desarrollador).

## Restricciones

- las transiciones provienen de `.ai/config/orchestrator.yaml`, no de codigo;
- `better-sqlite3` ya instalado y autorizado en `FitFlow-ai`;
- no crear commits, no tocar secretos ni `.env`, no instalar dependencias.

## Criterios de aceptacion

| ID | Criterio | Evidencia esperada |
| --- | --- | --- |
| AC-1 | State Machine valida contra orchestrator real | tests core PASS |
| AC-2 | DONE requiere `PENDING_ACCEPTANCE` + actor `developer` | guard en StateMachine |
| AC-3 | Run Store persiste eventos y estado en filesystem | tests core PASS |
| AC-4 | proyeccion SQLite consultable | tests core PASS |

## Impacto documental

`canonical_update` de `docs/ai/cli-contract.md` y nota en `roadmap-vnext.md`.
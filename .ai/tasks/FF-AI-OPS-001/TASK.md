---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-AI-OPS-001
title: Activar el workflow operacional determinista y acotado por contexto
status: PENDING_ACCEPTANCE
task_type: tooling
area: ai_tooling
scope: mixed
lane: ai_orchestrated
risk: medium
priority: P0
created_at: 2026-08-26T00:00:00Z
author_role: developer
baseline:
  revision: 4ac8ce9fffaa4a77e04fce435035f341767d6cf0
  fingerprint_status: unavailable
  working_tree_fingerprint: null
  fingerprint_reason: multi-repository task uses explicit repository revisions
github_issue: null
openspec_change: operational-workflow-mvp
objective: Activar un workflow local determinista que valide la Task, incorpore evidencia OpenSpec de solo lectura, limite el contexto antes del runtime y persista eventos y RunState sin usar APIs pagas.
in_scope:
  - Tecnotron-ai runner y adapters para Task, OpenSpec, repo-packager y RunStore
  - Entrega del contexto acotado al Agent Runtime
  - Bootstrap OpenSpec y configuracion consumidora en FitFlow
  - Modo simulate local sin inferencia ni API
  - Pruebas y telemetria de contexto correlacionable por run
  - Linea zero-cost observada por uso, con Planner y Coder Strong A habilitados
out_of_scope:
  - Aceptacion terminal, merge, push o promocion a DONE
  - Provider o modelo real
  - Paid API, Temporal, MCP o retrieval semantico
  - Mutaciones de producto, base de datos o secretos
  - Automatizacion completa de Orca o GitHub
constraints:
  - Orca conserva workspace y sesion; Task Lifecycle conserva estados y aceptacion
  - OpenSpec solo aporta especificaciones y deltas como evidencia
  - repo-packager materializa; ContextPackager y Explorer deciden suficiencia
  - FitFlow y Tecnotron-ai usan worktrees emparejados y ownership disjunto
  - No se agregan dependencias al manifiesto
acceptance_criteria:
  - id: AC-1
    criterion: El CLI valida Project Profile, Task y registries antes de ejecutar etapas
    evidence: tests/integration/operational-runner.test.js
  - id: AC-2
    criterion: OpenSpec se consulta por comandos JSON de solo lectura y su delta entra al contexto
    evidence: tests/adapters/operational.test.js y openspec validate
  - id: AC-3
    criterion: El contexto respeta un budget duro y conserva requested included omitted y missing
    evidence: tests/integration/operational-runner.test.js
  - id: AC-4
    criterion: El runtime recibe exclusivamente la Task y la evidencia incluida por ContextPackager
    evidence: tests/core/agent-mvp.test.js y tests/core/agent-runtime.test.js
  - id: AC-5
    criterion: El modo simulate persiste artifacts eventos idempotentes y RunState sin llamadas pagas
    evidence: tests/integration/operational-runner.test.js
  - id: AC-6
    criterion: repo-packager ofrece materializacion exacta JSON sin cache ni npx
    evidence: tests/repo-packager/pack.test.py
  - id: AC-7
    criterion: Cada rol habilitado usa una linea zero-cost con invocacion observada, Ox Alpha queda unavailable y HIGH conserva su gate
    evidence: tests/integration/operational-runner.test.js y tests/core/routing.test.js
ownership_keys:
  - path:.ai/tasks/FF-AI-OPS-001/**
  - path:.ai/runs/FF-AI-OPS-001-*/**
  - path:openspec/**
  - config:.ai/config/project-profile.yaml
  - config:.ai/config/models.yaml
  - config:.ai/config/finops.yaml
  - config:.ai/config/roles.yaml
  - path:FitFlow-ai/src/operational-runner/**
  - path:FitFlow-ai/src/adapters/**
  - path:FitFlow-ai/src/project-profile/index.js
  - path:FitFlow-ai/src/agent-mvp/index.js
  - path:FitFlow-ai/src/agent-runtime/index.js
  - path:FitFlow-ai/src/core/run-store.js
  - path:FitFlow-ai/scripts/workflow/**
  - path:FitFlow-ai/scripts/doctor/tests/doctor.test.js
  - path:FitFlow-ai/tests/**
  - path:FitFlow-ai/.opencode/skills/repo-packager/scripts/pack.py
  - path:FitFlow-ai/package.json
  - path:FitFlow-ai/docs/research/temporary-ox-alpha-free-line.md
required_docs:
  - AGENTS.md
  - docs/SOURCE_OF_TRUTH.md
validation_expected:
  - openspec validate operational-workflow-mvp --strict
  - python tests/repo-packager/pack.test.py
  - node --test tests/core tests/adapters tests/integration/operational-runner.test.js
  - git diff --check
document_impact:
  - openspec/changes/operational-workflow-mvp
  - Tecnotron-ai current-state and roadmap follow-up after acceptance
---

# Objetivo

Activar el spine operacional ya definido sin colapsar responsabilidades ni
enviar corpus amplios al runtime. El primer modo ejecutable es una simulacion
local declarada que produce artifacts reales y deja cualquier inferencia real
detras de `AgentRuntimePort`.

## Repositorios y worktrees

- FitFlow: `feat/FF-AI-OPS-001`, base `develop@4ac8ce9`.
- Tecnotron-ai: `mauedgar/FF-AI-OPS-001`, base `tooling@141174b`.

## Gate

La implementacion termina en evidencia para revision y aceptacion del
Developer. No emite `DONE`, no integra y no limpia los worktrees.

## Aceptacion (append-only)

- 2026-08-26: el Developer confirma los cambios y autoriza crear los PRs. La
  validacion y el review son `PASS`/`ACCEPT`; integracion y `DONE` permanecen
  pendientes. PRs abiertos:
  `https://github.com/mauedgar/tecnotron-ai/pull/21` y
  `https://github.com/mauedgar/FitFlow/pull/13`.

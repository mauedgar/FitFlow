---
artifact: TASK
task_id: FF-DOC-AI-BOUNDARY-001
title: Delimitar contratos del producto y del AI Core
status: PENDING_ACCEPTANCE
task_type: docs
scope: docs_tooling
lane: ai_orchestrated
risk: medium
priority: P1
branch: docs/FF-DOC-AI-BOUNDARY-001
worktree: C:/Proyectos-Web/FitFlow.worktrees/FF-DOC-AI-BOUNDARY-001
baseline: 4ac8ce9fffaa4a77e04fce435035f341767d6cf0
ownership_keys:
  - doc:ai-core-contract-boundary
  - path:docs/SOURCE_OF_TRUTH.md
  - path:docs/ai/README.md
  - path:docs/ai/context-artifacts.md
  - path:docs/process/information-artifacts.md
  - path:.ai/contracts/README.md
  - path:.ai/tasks/FF-DOC-AI-BOUNDARY-001/**
validation: PASS
review_verdict: ACCEPT
developer_acceptance: ACCEPTED
integration: NOT_INTEGRATED
---

# Objetivo

Aclarar la frontera entre los contratos Pydantic/OpenAPI del producto y los
JSON Schema v2 usados para el intercambio operativo con FitFlow-ai, sin
modificar schemas ni adelantar una decision de distribucion pendiente.

# Alcance

- declarar la autoridad de FitFlow sobre los contratos web del producto;
- declarar la autoridad de FitFlow-ai sobre Zod, runtime y politica generica;
- clasificar `.ai/contracts/v2/` como snapshot consumidor del baseline;
- registrar que npm, submodulo u otro mecanismo siguen `MIGRATION_PENDING`;
- aclarar que el bloqueo afecta la evolucion contractual IA, no el desarrollo
  normal del producto desde `develop`;
- producir validacion, review independiente y resultado documental.

# Fuera de alcance

- modificar JSON Schema, Zod, estados, transiciones o `ReviewResult`;
- elegir o implementar el mecanismo de distribucion;
- modificar backend, frontend, configuracion activa o tooling;
- resolver divergencias contractuales pendientes.

# Criterios de aceptacion

- [x] AC-1: Source of Truth distingue contratos web y operativos.
- [x] AC-2: ownership proveedor/consumidor queda explicito y consistente.
- [x] AC-3: `MIGRATION_PENDING` no se presenta como capacidad implementada.
- [x] AC-4: desarrollo de producto no queda bloqueado por la integracion IA.
- [x] AC-5: no cambian schemas, codigo ni configuracion activa.
- [x] AC-6: diff documental valida y recibe review independiente.

# Documentos requeridos

- `AGENTS.md`;
- `docs/SOURCE_OF_TRUTH.md`;
- `docs/ai/README.md`;
- `docs/ai/context-artifacts.md`;
- `docs/process/information-artifacts.md`;
- `.ai/contracts/README.md`;
- `FitFlow-ai/AGENTS.md`;
- `FitFlow-ai/docs/SOURCE_OF_TRUTH.md`;
- `FitFlow-ai/docs/architecture.md`;
- `FitFlow-ai/docs/implementation-roadmap.md`.

# Autoridad

El Developer autorizo esta task docs-only y el ciclo worktree, PR, integracion
en `develop` y cleanup el 2026-08-25. La ejecucion documenta el resultado sin
resolver decisiones pendientes del repositorio FitFlow-ai.

# Aceptacion

La validacion es `PASS` y el review independiente es `ACCEPT`, sin findings
bloqueantes. El Developer confirma la integracion y cleanup de tasks completas
el 2026-08-26. Merge, `DOC_SYNC` y `DONE` permanecen pendientes hasta evidencia
verificable.

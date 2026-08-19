---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-AI-VNEXT-001
title: Adoptar baseline vNext de asistencia IA
status: PENDING_ACCEPTANCE
task_type: migration
area: ai_tooling
scope: docs_tooling
lane: mixed
risk: medium
priority: P0
created_at: "2026-08-18T00:00:00-03:00"
author_role: developer
baseline:
  revision: 3f3021b2cf26c5839feb428a50b59e1116f283a0
  fingerprint_status: unavailable
  working_tree_fingerprint: null
  fingerprint_reason: "El arbol ya contenia cambios previos y no se capturo un fingerprint antes de iniciar la migracion."
github_issue: null
openspec_change: null
ownership_keys:
  - "doc:baseline-vnext"
  - "config:ai-v2"
  - "path:FitFlow-ai/docs"
required_docs:
  - AGENTS.md
  - docs/SOURCE_OF_TRUTH.md
  - docs/architecture.md
  - docs/current-state.md
  - docs/quality-and-validation.md
---

# Objetivo

Producir y adoptar la baseline vNext a partir de v4, los informes 01-05 y el
estado real del workspace, sin declarar implementadas capacidades pendientes.

## Scope

- doctrina, ADR y documentacion IA de FitFlow;
- configuracion, contracts, templates y backlog v2;
- arquitectura documental de FitFlow-ai;
- informes fuente y material para desarrolladores en DOCX;
- bundle versionado con hashes y evidencia.

## Fuera de scope

- implementar AI Core, adapters, State Machine o Agent MVP;
- instalar/actualizar dependencias;
- corregir el codigo iniciado en FF-AI-001;
- commits, push, merge o transicion DONE.

## Restricciones

- preservar cambios preexistentes no relacionados;
- usar `developer` en contratos v2 y registrar migracion desde v1;
- mantener source material fuera de machine context;
- tratar herramientas no reproducibles como `UNAVAILABLE` o pending.

## Criterios de aceptacion

| ID | Criterio | Evidencia esperada |
| --- | --- | --- |
| AC-1 | La matriz v4 -> vNext esta canonizada y trazable | MIGRATION + ADR 0014-0017 |
| AC-2 | Config y contratos v2 son parseables y coherentes | validate_vnext.py PASS |
| AC-3 | El backlog v4 queda superseded y existe secuencia vNext | backlog/vnext.yaml |
| AC-4 | FitFlow-ai refleja AI Core sin afirmar implementacion | docs del repo hermano |
| AC-5 | Source/developer material usa DOCX | structural/a11y audit |
| AC-6 | Existe bundle con MANIFEST SHA-256 | ZIP + MANIFEST |
| AC-7 | Existe review independiente y evidencia normalizada | REVIEW/VALIDATION/RESULT |

## Impacto documental

`canonical_update` y ADR 0014-0017.

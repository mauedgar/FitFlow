---
artifact: TASK
task_id: FF-LOCALvNext-000
title: Reforzar auditoria documental y operativa previa a Fase 3
status: PENDING_ACCEPTANCE
task_type: docs
area: docs
scope: docs_tooling
lane: mixed
risk: medium
priority: P0
branch: feat/FF-NEXT-000
worktree: C:/Users/maued/orca/workspaces/FitFlow/feat-FF-NEXT-000
baseline: 046fa1f34d3886c3dbdd4a2f6a5064c0fb2a759e
validation: PASS
review_verdict: ACCEPT_WITH_NON_BLOCKING_FINDINGS
developer_acceptance: PENDING
integration: NOT_INTEGRATED
ownership_keys:
  - path:.ai/tasks/FF-LOCALvNext-000/**
  - path:.ai/tasks/FF-LOCALvNext-001-adr-integrity/PLAN.md
  - domain:sprint-6.8-curation
allowed_write_scope:
  - .ai/tasks/FF-LOCALvNext-000/**
  - .ai/tasks/FF-LOCALvNext-001-adr-integrity/PLAN.md
---

# Objetivo

Corregir y reforzar la auditoria documental y operativa previa a la Fase 3 de
reconciliacion de tasks, sin ejecutar esa fase ni modificar producto o
documentacion canonica.

# Fase 3 gobernada

La unica Fase 3 referenciada por este ciclo es:

`.ai/tasks/FF-LOCALv-000/PLAN.md` -> `Fase 3 - Reconciliacion de tasks`.

No corresponde al Paso 3 de `.ai/tasks/FF-LOCALvNext-000/PLAN.md`.

# Alcance

- registrar baseline, branch, worktree, riesgo y ownership;
- corregir los planes `FF-LOCALvNext-000` y
  `FF-LOCALvNext-001-adr-integrity`;
- definir el bundle documental minimo para nuevas ejecuciones FitFlow;
- distinguir evidencia historica de revalidacion actual;
- aislar findings de Tecnotron/FitFlow-ai en `TECNOTRON_REVIEW.md`;
- producir `REVIEW.md`, `VALIDATION.md` y `RESULT.md` para este ciclo.

# Fuera de alcance

- ejecutar la Fase 3;
- implementar o modificar backend/frontend;
- editar documentacion canonica de FitFlow;
- editar Tecnotron/FitFlow-ai;
- modificar secretos, `.env`, DB o migraciones;
- merge, push, limpieza o eliminacion de ramas/worktrees;
- inventar evidencia historica.

# Responsabilidades

| Rol | Responsabilidad en este ciclo |
| --- | --- |
| Developer | decisiones, excepciones, secretos, aceptacion final e integracion |
| Lifecycle | branch/worktree, baseline, limpieza y gates Git deterministas |
| Agente ejecutor | cambios documentales dentro del allowed write scope y evidencia |
| Reviewer | revision semantica independiente |
| Validator | validacion determinista y reproducible |

# Criterios de aceptacion

- [x] `feat/FF-NEXT-000` fue creado limpio y su baseline es verificable.
- [x] Toda referencia a Fase 3 apunta inequívocamente a `FF-LOCALv-000`.
- [x] `risk: medium`, ownership y allowed write scope quedan registrados.
- [x] El plan distingue evidencia historica de revalidacion actual.
- [x] El bundle futuro incluye TASK/PLAN cuando aplique, REVIEW, VALIDATION y RESULT.
- [x] No se copian contratos ni arquitectura interna de Tecnotron.
- [x] Todo finding externo queda aislado en `TECNOTRON_REVIEW.md`.
- [x] `FF-LOCALvNext-001-adr-integrity` permanece `BLOCKED`.
- [x] La Fase 3 no se ejecuta durante este ciclo.
- [x] Review independiente y validacion determinista quedan registradas.

# Validacion esperada

- `git status -sb`
- `git branch --show-current`
- `git worktree list`
- `git diff --check`
- `git diff --stat`
- `git diff`
- comprobaciones textuales de Fase 3, riesgo, ownership, bundle y estado bloqueado

# Gate de salida

El ciclo termina en `PENDING_ACCEPTANCE`. Solo el Developer puede aceptar la
integracion. `PHASE_3_READY` requiere que todos los criterios estructurales del
plan corregido esten satisfechos; no autoriza ejecutar la Fase 3 en este ciclo.

El ownership y allowed write scope de `FF-LOCAL-001..010` no pertenecen a este
run preparatorio. Lifecycle debe materializarlos y bloquearlos de forma
explicita antes de la futura ejecucion de Fase 3.

# Compatibilidad machine-readable

El identificador historico `FF-LOCALvNext-000` no satisface actualmente el
patron exclusivamente mayusculo de `.ai/contracts/v2/common.schema.json`. Este
ciclo no renombra la task ni modifica el schema. Las vistas Markdown son la
evidencia producida; cualquier JSON v2 se reporta `UNAVAILABLE` hasta que una
decision separada resuelva la compatibilidad sin perder identidad.

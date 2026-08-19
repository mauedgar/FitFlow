---
document_id: FF-ADR-0016
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-18
---

# ADR 0016: GitHub y OpenSpec como capas separadas

## Decision

Usar un unico GitHub Project para FitFlow, con Issues, PR y Actions como plano
de control del desarrollador. La Issue es TASK principal cuando existe
sincronizacion; `.ai/tasks` es espejo local y fallback offline autorizado.

OpenSpec se adopta para especificaciones y deltas funcionales. No reemplaza
TASK, Project, State Machine, artefactos de run ni ADR.

## Autoridad

Los artefactos JSON de `.ai/runs/<run_id>/` son evidencia durable. GitHub
comments/checks son visualizacion. Una integracion debe evitar dos fuentes con
igual autoridad y ser idempotente.

## Estado

Las CLIs `gh` y `openspec` no estan disponibles en el shell verificado. La
decision no declara implementados sus adapters.

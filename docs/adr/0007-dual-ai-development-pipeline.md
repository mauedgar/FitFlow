---
document_id: FF-ADR-0007
status: superseded
machine_context: false
indexing: excluded
superseded_by: FF-ADR-0011
---

# ADR 0007: Dos pipelines complementarios de desarrollo con IA

- **Estado:** Superseded por ADR 0011
- **Fecha:** 2026-08-12
- **Reemplazado:** 2026-08-16

## Contexto histórico

Se había decidido mantener un pipeline principal y una rama local diaria con
un segundo orquestador. Esa separación dejó de representar la arquitectura
elegida.

## Decisión histórica

La versión v3 definía dos pipelines independientes y un mapa de repositorio
propio de una herramienta descartada.

## Motivo del reemplazo

Codebase pasa a ser la superficie única de orquestación. Los modelos convergen
mediante roles y un adaptador neutral. La estructura se obtiene con inventarios,
Repomix, índice vectorial.

ADR 0011 gobierna el proceso activo. Este archivo se conserva solo para
trazabilidad y no debe seleccionarse como instrucción de tarea.

---
document_id: FF-AI-PROJECT-PROFILE-001
status: canonical
machine_context: true
version: 1.1
updated: 2026-08-21
---

# Project Profile y OpenSpec

## Project Profile

`.ai/config/project-profile.yaml` adapta AI Core a FitFlow y permanece bajo
ownership del producto. Declara roots, docs, arquitectura, scopes, ownership
keys, risk signals, comandos, GitHub labels, paths de runs y feature flags.

Los paths fisicos no constituyen por si mismos un resolver cross-repo portable.
FitFlow declara el root externo mediante Project Profile; la resolucion portable
y adapters genericos pertenecen a Tecnotron-ai. FitFlow no introduce un segundo
resolver ni duplica el estado interno de esas implementaciones.

El core no contiene excepciones especificas de Booking, RRULE, frontend o
estructura de carpetas. Esas reglas pertenecen al perfil versionado.

## OpenSpec

OpenSpec se adopta como capa de especificacion funcional cuando su bootstrap y
compatibilidad se validen. Puede describir deltas, propuestas, tareas de cambio
funcional y archivo de specs aceptadas.

No reemplaza:

- GitHub Issue/TASK como unidad operativa;
- State Machine y retries;
- artefactos de run;
- validacion, review o aceptacion;
- docs/ADR para decisiones arquitectonicas.

## Estado

La disponibilidad de `gh` u OpenSpec no define el estado interno de los
adapters de Tecnotron. Este documento gobierna exclusivamente la configuracion e
integracion especificas de FitFlow.

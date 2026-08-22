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

Los paths fisicos actuales no constituyen un resolver cross-repo portable. Su
resolucion desde Orca o el Project Profile pertenece a `FF-AI-VNEXT-005`; no se
introduce un segundo resolver en FitFlow.

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

La CLI OpenSpec esta disponible en el baseline verificado. Bootstrap y adapter
permanecen pendientes en `FF-AI-VNEXT-005`; disponibilidad no equivale a
integracion implementada.

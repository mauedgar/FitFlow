---
document_id: FF-ROADMAP-001
status: canonical
machine_context: true
version: 5.1
updated: 2026-08-21
---

# Roadmap de FitFlow

## Principio

El tooling reduce incertidumbre y repetición; no bloquea el MVP ni adquiere
autoridad sobre el producto.

## Producto

| Prioridad | Objetivo |
| --- | --- |
| P0 | preservar el baseline Sprint 6.8 y cerrar discrepancias críticas |
| P1 | MVP Cliente -> Agenda -> Sesión -> Reserva -> Front Desk |
| P2 | ampliar unit/integration/API/concurrency y estabilizar Alembic/frontend |
| P3 | entorno reproducible, logging, staging y beta controlada |
| P4 | asistencia avanzada, métricas, facturación y automatizaciones |

## Plataforma de desarrollo asistido

FitFlow-ai posee el roadmap detallado del AI Core. El estado de integracion que
afecta al producto es: `FF-AI-VNEXT-001` a `004` `DONE`,
`FF-AI-VNEXT-005` `NEXT` y `FF-AI-VNEXT-006` `READY`. Consultar
`docs/implementation-roadmap.md` en FitFlow-ai para secuencia, dependencias y
gates; FitFlow no mantiene una segunda copia.

## Autonomía

Los agentes pueden explorar, editar scope acotado y ejecutar validaciones
permitidas. El desarrollador decide arquitectura/dominio, dependencias, seguridad,
migraciones destructivas, ampliación del MVP, promoción documental y aceptación
final.

## Paralelismo

Solo tareas sin ownership cruzado. La velocidad no justifica dos writers sobre
la misma ruta, contrato, dominio, DB/migración o documento canónico.

---
document_id: FF-ROADMAP-001
status: canonical
machine_context: true
version: 5.2
updated: 2026-09-22
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

Tecnotron-ai posee su roadmap y estado interno. FitFlow no mantiene una segunda
secuencia de work packages, TASKs o estados de implementacion del sistema de
desarrollo. FitFlow solo planifica aqui trabajo que modifica el producto o una
integracion de la cual FitFlow sea owner.

Cuando una tarea de FitFlow dependa de un estado concreto de Tecnotron, debe
referenciar explicitamente el repositorio y revision observados; esa referencia
no transfiere ownership ni convierte el roadmap externo en roadmap de FitFlow.

## Autonomía

Los agentes pueden explorar, editar scope acotado y ejecutar validaciones
permitidas. El desarrollador decide arquitectura/dominio, dependencias, seguridad,
migraciones destructivas, ampliación del MVP, promoción documental y aceptación
final.

## Paralelismo

Solo tareas sin ownership cruzado. La velocidad no justifica dos writers sobre
la misma ruta, contrato, dominio, DB/migración o documento canónico.

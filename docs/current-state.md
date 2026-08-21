---
document_id: FF-STATE-001
status: canonical
machine_context: true
version: 5.1
snapshot: 2026-08-21
---

# Estado actual de FitFlow

## Producto confirmado

- Sprint 6.8 consolidado hasta `FF-LOCAL-010`.
- Backend con FastAPI async, SQLAlchemy 2.x Async, Pydantic v2 y PostgreSQL.
- RRULE es la unica fuente de recurrencia; genera faltantes futuros en horizonte
  de 15 dias y persiste sesiones en UTC.
- Booking admite resolucion por sesion o agenda, protege capacidad, conserva
  cancelaciones y no cuenta reservas canceladas como cupo.
- ClassSession conserva soft delete administrativo e historia.
- Front Desk usa un service unico y check-in `confirmed -> attended` con
  `checked_in_at`.
- La arquitectura objetivo del producto continua siendo monolito modular por
  bounded contexts, con migracion gradual y fitness functions.

## Validacion confirmada

- Harness en `backend/tests/` y base exclusiva `fitflow_test`.
- Pruebas dirigidas de metadata, mappers, RRULE, Booking, cancelacion,
  capacidad, check-in y Redis.
- Ruff y Pyright existen en la imagen de tests.
- La suite HTTP integral del MVP no esta demostrada.

## Plataforma de asistencia IA

FitFlow-ai es un repositorio independiente y la Source of Truth de su estado
interno. FitFlow solo conserva este resumen de integracion:

- baseline vNext aceptada; `FF-AI-VNEXT-001` a `004` estan `DONE` por decision
  del desarrollador;
- `repo-packager` fue reparado e integrado mediante el PR #2 de FitFlow-ai;
- `FF-AI-VNEXT-005` es el siguiente bloque (`NEXT`) y
  `FF-AI-VNEXT-006` fue reactivado (`READY`); conformance ContextPackager v2
  sigue pendiente;
- Orca controla workspace y sesion; Git worktree aisla la escritura;
- OpenCode es el Agent Runtime preferido actual e intercambiable; su adapter y
  conformance siguen pendientes;
- GitHub reemplaza a Jira para planificacion, integracion y validacion; los
  adapters GitHub/OpenSpec siguen pendientes;
- Project Profile, TASK, runs, contratos de intercambio y configuracion
  especifica permanecen en FitFlow.

El detalle vigente se consulta en `docs/current-state.md` y
`docs/implementation-roadmap.md` del repositorio FitFlow-ai. No se replica aqui.

## Deuda activa

- cobertura API integral y fixtures HTTP async compartidas;
- refactors de fronteras heredadas;
- resolver roots portables y consumers cross-repo en `FF-AI-VNEXT-005`;
- migrar el backlog vNext al ownership de FitFlow-ai sin romper consumidores;
- verificar adapters OpenCode, GitHub/OpenSpec y modelo Explorer;
- medir contexto, calidad y retrabajo antes de ampliar autonomia.

---
document_id: FF-STATE-001
status: canonical
machine_context: true
version: 5.2
snapshot: 2026-09-22
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
- Booking HTTP usa la capacidad de la `ClassSession` materializada para decidir
  disponibilidad y preserva el boundary transaccional validado.
- `GET /class-sessions/{id}/availability` reporta `capacity_snapshot` de la
  sesion, no la capacidad mutable de la agenda.
- Front Desk usa un service unico y check-in `confirmed -> attended` con
  `checked_in_at`.
- La arquitectura objetivo del producto continua siendo monolito modular por
  bounded contexts, con migracion gradual y fitness functions.

## Validacion confirmada

- Harness en `backend/tests/` y base exclusiva `fitflow_test`.
- Pruebas dirigidas de metadata, mappers, RRULE, Booking, cancelacion,
  capacidad, check-in y Redis.
- Ruff y Pyright existen en la imagen de tests.
- El vertical HTTP minimo de Booking y ClassSession tiene cobertura API
  determinista publicada; la evidencia mas reciente del bounded vertical cerro
  con la suite backend completa en 58 tests `PASS`. Esto no afirma cobertura
  exhaustiva de todo el producto.

## Plataforma de asistencia IA

Tecnotron-ai es un repositorio independiente y autoridad de su arquitectura,
roadmap, tooling y estado interno. FitFlow conserva unicamente configuracion,
contratos consumidores y evidencia especifica del producto.

- Project Profile, TASK, runs, contratos de intercambio y configuracion
  especifica permanecen en FitFlow.
- Orca/OpenCode y otras superficies son implementaciones reemplazables del
  sistema de desarrollo; no adquieren autoridad sobre FitFlow.
- El estado interno de Tecnotron no se replica como backlog o roadmap canonico
  de FitFlow. Las referencias cross-repo deben declarar un ref/commit cuando
  necesiten un snapshot exacto.
- Los hallazgos de Programmatic Process son evidencia de investigacion sin
  transferencia automatica de ownership, lifecycle o arquitectura a FitFlow.

## Deuda activa

- cobertura API integral y fixtures HTTP async compartidas;
- refactors de fronteras heredadas;

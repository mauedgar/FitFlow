---
document_id: FF-STATE-001
status: canonical
machine_context: true
version: 5.3
snapshot: 2026-11-01
---

# Estado actual de FitFlow

## Producto backend (observacion historica del 2026-09-22)

Los hechos backend siguientes describen el corte del 22 de septiembre; este
snapshot no los revalida ni afirma que sean el estado backend mas reciente.

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

## Validacion backend (observacion historica del 2026-09-22)

- Harness en `backend/tests/` y base exclusiva `fitflow_test`.
- Pruebas dirigidas de metadata, mappers, RRULE, Booking, cancelacion,
  capacidad, check-in y Redis.
- Ruff y Pyright existen en la imagen de tests.
- El vertical HTTP minimo de Booking y ClassSession tiene cobertura API
  determinista publicada; la evidencia mas reciente del bounded vertical cerro
  con la suite backend completa en 58 tests `PASS`. Esto no afirma cobertura
  exhaustiva de todo el producto.

## Frontend Admin (corte del 2026-11-01)

- PR #34 integrado en `develop` en el commit
  `2557e9066eae504c47fa166904694f0d1d2c0641` (tree
  `4160747ea2784c58817957f49a9d989f822cf315`); candidato integrado
  `75830c8c01d62f03bf1cf0fbbd369c4a963e33b4`. Los refs y el merge
  constan en Git local.
- Segun el recibo operativo comunicado para este corte, Issue #33 esta
  `CLOSED` e IR003 dio `PASS_SHELL_UI_WITH_LIMITATIONS` para el shell Admin:
  24/24 tests frontend y navegador con datos en memoria/mocks en anchos
  320, 390, 768, 1024, 1280 y 1440 px. No equivale a autenticacion real E2E.
- Segun el mismo corte operativo, Issue #25 permanece `OPEN` y
  `REAL_AUTH_E2E` en `NOT_RUN`. Estos estados de Issues y el resultado IR003
  no se verifican mediante refs Git; requieren sus recibos operativos para
  confirmacion independiente. No se infiere cierre de esa deuda del merge.

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

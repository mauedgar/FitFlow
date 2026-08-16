---
document_id: FF-STATE-001
status: canonical
machine_context: true
version: 4.0
snapshot: 2026-08-16
---

# Estado actual de FitFlow

## Producto confirmado

- Sprint 6.8 consolidado hasta `FF-LOCAL-010`.
- Backend con FastAPI async, SQLAlchemy 2.x Async, Pydantic v2 y PostgreSQL.
- RRULE es la única fuente de recurrencia; genera faltantes futuros en horizonte
  de 15 días y persiste sesiones en UTC.
- Booking admite resolución por sesión o agenda, protege capacidad, conserva
  cancelaciones y no cuenta reservas canceladas como cupo.
- ClassSession conserva soft delete administrativo e historia.
- Client, GymClass y ClassSchedule usan bajas conservativas; Membership cambia
  de estado.
- Front Desk usa un service único y check-in `confirmed -> attended` con
  `checked_in_at`.
- Las rutas públicas de GymClass, Teacher y ClassSchedule preceden a rutas UUID.
- `UserRole` es el mecanismo funcional. Role/Permission granular permanece draft.

## Validación confirmada

- Harness en `backend/tests/` y base exclusiva `fitflow_test`.
- Pruebas dirigidas de metadata, mappers, RRULE, Booking, cancelación,
  capacidad, check-in y Redis.
- Ruff y Pyright existen en la imagen de tests.
- La suite HTTP integral del MVP no está demostrada.

## Plataforma de IA

Estado: `DESIGNED_NOT_IMPLEMENTED`.

- Bundle documental v4 preparado.
- Codebase seleccionado como superficie de orquestación.
- Repomix disponible como snapshot acotado.
- Dependencias de LlamaIndex/Qdrant declaradas instaladas por el equipo, pero su
  compatibilidad y ejecución aún no están verificadas por este baseline.
- Repomix, inventarios automáticos, XML estructural, índice vectorial,
  Phoenix, Promptfoo, hooks y MCP no se declaran funcionales.

## Deuda activa

- cobertura API integral y fixtures HTTP async compartidas;
- refactors de fronteras heredadas;
- auditoría de compatibilidad del entorno `env_tools`;
- implementación y evaluación del sistema de contexto;
- adaptador comprobado para Codebase;
- métricas antes de ampliar autonomía o presupuesto.

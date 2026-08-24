---
id: FF-LOCAL-006
title: Alinear contratos Pydantic v2 con el dominio consolidado
status: Done
priority: High
area: backend
execution_lane: codex
type: refactor
baseline_revision: REVIEWED
depends_on: [FF-LOCAL-005]
---
Objetivo

Consolidar schemas Pydantic v2 como contratos claros de entrada, update, salida pública, uso interno y vistas operativas, sin mover business rules dependientes de DB a Pydantic.

# Contexto mínimo

Leer `AGENTS.md`, arquitectura, dominio, current-state, ADR Pydantic v2, `backend/app/core/enums.py` y modelos ORM ya consolidados.

# Scope

- `backend/app/schemas/`
- imports de enums/tipos
- routers/services sólo como consumidores
- tests schemas/API

# Convenciones

Usar cuando correspondan:

- `<Entity>Create`
- `<Entity>Update`
- `<Entity>Public`
- `<Entity>Internal`
- vistas funcionales (`FrontDesk...`, `Mini`, `WithStats`) sólo si tienen consumidor real

# Responsabilidad Pydantic

Sí: tipos, shape, required/optional, bounds, formato, validación estructural/cross-field sin DB, serialización y respuestas.
No: membership real, capacidad real, permisos persistidos, resolver schedule-&gt;session ni compatibilidad de allowed_plan con membership.

# Caso BookingCreate

Verificar `class_schedule_id XOR class_session_id`: exactamente uno cuando ese contrato siga vigente. Resolución y business rules permanecen en Service.

# Enums

Reutilizar `backend/app/core/enums.py`; no duplicarlos en schemas.

# Auditoría previa

Matriz:
`entidad | Create | Update | Public | Internal | Views | consumidores | problemas`

Antes de eliminar/renombrar un schema buscar imports, routers, services, OpenAPI, frontend y tests.

# Criterios de aceptación

- [ ] roles de schemas claros
- [ ] Pydantic v2 consistente
- [ ] validaciones estructurales separadas de business rules
- [ ] Booking XOR verificado o A_REVIEW
- [ ] enums comunes provienen de core/enums.py
- [ ] response models coherentes
- [ ] tests schemas/API actualizados
- [ ] Ruff/type-check ejecutados
- [ ] OpenAPI revisado si cambia contrato público

# Validaciones

- pytest unit/schema: required
- pytest api targeted: si cambia HTTP
- Ruff: required
- type-check: required
- OpenAPI review: si cambia schema público

# Impacto documental

Puede actualizar `domain.md`, `current-state.md` o `architecture.md`. ADR 0006 sólo si cambia la decisión.
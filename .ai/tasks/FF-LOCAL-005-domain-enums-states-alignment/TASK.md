---
id: FF-LOCAL-005
title: Auditar y alinear enums y estados funcionales del dominio
status: Ready
priority: High
area: backend
execution_lane: codex
type: refactor
baseline_revision: pending
depends_on: [FF-LOCAL-004]
---

# Objetivo
Inventariar y alinear los enums/estados funcionales reales de FitFlow manteniendo conceptos distintos separados aunque compartan valores.

Archivo canónico actual a verificar:
`backend/app/core/enums.py`

No moverlo por iniciativa propia.

# Principios aceptados
- mantener estados funcionales explícitos y estables
- `MembershipPlan` y `AllowedPlan` permanecen separados conceptualmente
- compartir valores no implica redundancia
- `MembershipPlan` = plan que posee el cliente
- `AllowedPlan` = planes que una oferta/schedule admite
- no agregar/eliminar valores sólo para hacer coincidir docs con código

# Scope
`app/core/enums.py` y consumidores en models, schemas, services, CRUD, routers, tests, migraciones y frontend sólo para verificar contratos.

# Fase A — Inventario
Matriz:
`enum | valor | definición | consumidores | persistencia | API/frontend | estado`

Clasificación: `CONFIRMED`, `MISSING`, `REDUNDANT`, `LEGACY`, `A_REVIEW`.

Revisar como mínimo:
- UserRole
- DifficultyLevel
- BookingStatus
- MembershipPlan
- MembershipStatus
- ActivityType
- AllowedPlan
- ClassSessionStatus

# Casos explícitos
## ClassSessionStatus
Verificar funcionalmente: `draft`, `scheduled`, `open`, `closed`, `cancelled`, `completed`.
No eliminar `draft` por discrepancia documental. Determinar uso, persistencia y transiciones.

## AllowedPlan
Mantener separado de MembershipPlan. Verificar si la ausencia de `gym_only` es intencional, omisión real o no aplicable. No agregarlo sin evidencia.

## UserRole
Verificar `admin`, `teacher`, `client`, `front_desk` y completar docstring si corresponde.

# Strings hardcodeados
Buscar equivalentes de roles/status/plans/activity/difficulty fuera de enums. Sustituir sólo cuando sea inequívoco y no altere persistencia/contratos.

# Fase B — Implementación
- completar faltantes demostrables
- retirar legacy sólo con evidencia/compatibilidad
- normalizar consumidores seguros
- mejorar docstrings
- agregar/actualizar tests

# Restricciones
No mover enums, fusionar AllowedPlan/MembershipPlan, inventar estados ni introducir una state machine nueva.

# Criterios de aceptación
- [ ] inventario completo
- [ ] estados/strings relevantes clasificados
- [ ] `draft` resuelto por evidencia
- [ ] AllowedPlan documentado como concepto separado
- [ ] `gym_only` resuelto por evidencia
- [ ] roles/estados con significado funcional claro
- [ ] impacto de persistencia explícito
- [ ] tests + Ruff + type-check ejecutados

# Validaciones
- pytest targeted: required
- Ruff: required
- type-check: required
- Alembic impact review: si cambia un enum persistido

# Impacto documental
Puede actualizar `domain.md` y `current-state.md`. ADR sólo si surge una nueva decisión durable.

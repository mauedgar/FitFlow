---
id: FF-LOCAL-007
title: Consolidar ClassSchedule y ClassSession
status: Done
priority: High
area: backend
execution_lane: codex
type: feature
baseline_revision: pending
depends_on: [FF-LOCAL-006]
---

# Objetivo
Consolidar `ClassSchedule -> ClassSession` y resolver explícitamente el estado real de RRULE, generación, temporalidad, capacidad y estados operativos.

**Comenzar en Plan mode antes de implementar.**

# Contexto mínimo
Leer `AGENTS.md`, dominio, arquitectura, current-state, quality/validation, ADR RRULE, enums auditados y código/tests de schedule/session.

# Fase 0 — Plan obligatorio
Antes de editar:
1. localizar implementación real
2. describir flujo actual
3. comparar con ADR/target
4. identificar legacy/gaps
5. proponer cambios mínimos
6. identificar impacto en Booking
7. definir tests

No asumir que RRULE ya está implementado.

# Scope
- ClassSchedule model/schema/service/CRUD/router
- ClassSession model/schema/service/CRUD/router
- generación de sesiones
- tests unit/integration/API asociados

# Fuera de scope
Booking general, Front Desk completo, rediseño Membership, naming no aprobado, microservicios/eventing, frontend salvo contrato imprescindible.

# RRULE
Determinar:
- si `rrule` existe
- si `days_of_week` u otro legacy sigue activo
- consumidores del legacy
- impacto de migración/compatibilidad
- si puede eliminarse sin pérdida relevante

No eliminar datos/columnas automáticamente.

# ClassSchedule
Verificar: gym_class, teacher, recurrencia, start_time, duración, capacity, start/end date, allowed_plan, auditoría y conflictos relevantes.

# ClassSession
Verificar: schedule relation, starts/ends, status, `capacity_snapshot`, disponibilidad derivada, relación Booking y estados de `app/core/enums.py`.

Consumir el resultado de FF-LOCAL-005: no asumir que `draft` sobra.

# Generación objetivo
`ClassSchedule -> validar -> interpretar RRULE -> ocurrencias dentro de vigencia -> conflictos -> ClassSession -> capacity_snapshot`

No duplicar ocurrencias ni generar fuera de ventana.

# Temporalidad
Verificar significado de start_time, timezone configurada, UTC cuando corresponda y mezcla naive/aware.

# AllowedPlan
Usar el enum auditado. La compatibilidad con Membership real sigue perteneciendo a Service/Booking.

# Testing
Unit: recurrencia/ventana/reglas puras.
Integration: generación, snapshot, no duplicación, persistencia.
API: contratos si cambian.

# Criterios de aceptación
- [ ] implementación RRULE/legacy inventariada
- [ ] RRULE implementado o bloqueo real explícito
- [ ] una única fuente de recurrencia acordada
- [ ] capacity_snapshot preservado
- [ ] estados alineados con core/enums.py
- [ ] temporalidad coherente
- [ ] duplicación/conflictos tratados
- [ ] allowed_plan correctamente ubicado
- [ ] tests targeted + Ruff + type-check pasan
- [ ] Booking no se refactoriza fuera de scope
- [ ] current-state actualizado con estado real

# Validaciones
- pytest unit targeted: required
- pytest integration targeted: required
- pytest api: si cambia contrato
- pytest broader backend: recomendado
- Ruff: required
- type-check: required
- Alembic review: si cambia persistencia
- OpenAPI review: si cambia contrato

# Impacto documental
Actualizar `current-state.md` y `domain.md`; `architecture.md` sólo si cambia el estado implementado. ADR RRULE sólo si se modifica la decisión.

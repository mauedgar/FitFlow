---
id: FF-LOCAL-004
title: Revisar integridad ORM y aplicar correcciones inequívocas
status: Ready
priority: High
area: backend
execution_lane: codex
type: audit
baseline_revision: pending
depends_on: [FF-LOCAL-003]
---

# Objetivo
Auditar integridad ORM después de la normalización y separar defectos demostrables, decisiones ambiguas y mejoras opcionales.

# Contexto mínimo
Leer `AGENTS.md`, `docs/architecture.md`, `docs/domain.md`, `docs/current-state.md`, `docs/quality-and-validation.md` y ADRs relevantes.

# Scope
- `backend/app/db/models/`
- base ORM
- migraciones sólo como evidencia
- schemas/services sólo para confirmar intención
- tests ORM/integration

# Fase A — Auditoría read-only
Producir una matriz:
`entidad | relación/campo | código actual | evidencia | clasificación | corrección propuesta`

Revisar:
- ForeignKey targets
- relationship / back_populates / backref
- cardinalidades
- nullable / unique / indexes
- cascade / delete behavior
- ownership
- imports circulares / forward refs
- mapper configuration

Clasificar: `CONFIRMED_DEFECT`, `CORRECT`, `A_REVIEW`, `OPTIONAL_IMPROVEMENT`, `LEGACY`.

# Human checkpoint
No aplicar decisiones ambiguas de cardinalidad, ownership, nullability con significado de negocio, cascade/delete, relaciones nuevas/eliminadas o migraciones destructivas sin aprobación humana.

# Fase B — Correcciones
Aplicar sólo defectos demostrados e inequívocos. No introducir diseño nuevo.

# Alembic
Si una corrección requiere migración, registrar impacto. No autogenerarla sólo porque cambió el modelo.

# Criterios de aceptación
- [ ] modelos principales auditados
- [ ] relaciones relevantes clasificadas
- [ ] mapper config sin errores no documentados
- [ ] decisiones ambiguas no resueltas silenciosamente
- [ ] correcciones con evidencia reproducible
- [ ] tests de integración actualizados cuando corresponda
- [ ] Ruff/type-check ejecutados
- [ ] impacto Alembic explícito

# Validaciones
- mapper/import smoke: required
- pytest targeted/integration: required cuando aplique
- Ruff: required
- type-check: required
- Alembic review: si corresponde

# Impacto documental
Puede actualizar `domain.md`, `current-state.md` o `architecture.md`. ADR sólo si cambia una decisión durable.

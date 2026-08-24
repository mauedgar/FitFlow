---
id: FF-LOCAL-003
title: Normalizar modelos ORM al estilo SQLAlchemy 2.x
status: Done
priority: High
area: backend
execution_lane: codex
type: refactor
baseline_revision: pending
depends_on: [FF-LOCAL-001]
---

# Objetivo
Normalizar los modelos ORM al estilo moderno de SQLAlchemy 2.x mejorando typing y consistencia sintáctica **sin cambiar la semántica actual**.

# Contexto mínimo
Leer `AGENTS.md`, `docs/architecture.md`, `docs/current-state.md`, `docs/domain.md`, `docs/quality-and-validation.md` e inspeccionar `backend/app/db/base_class.py`, `backend/app/db/base.py` y `backend/app/db/models/`.

# Scope
- `backend/app/db/models/`
- imports/anotaciones ORM directamente relacionadas
- base ORM sólo si una corrección mecánica inequívoca lo requiere

# Fuera de scope
No cambiar: nombres de tablas/columnas, tipos SQL, nullable, unique, defaults, FK targets, cardinalidades, cascade/delete behavior, ownership, enums, schemas, services, CRUD, routers ni migraciones.

# Transformaciones permitidas
- `DeclarativeBase`
- `Mapped[T]`
- `mapped_column()`
- `relationship()`
- typing de opcionales/colecciones
- imports modernos
- `TYPE_CHECKING`/forward refs
- retirar casts/ignores sólo si dejan de ser necesarios por esta normalización

# Regla de preservación
Antes y después debe conservarse el significado persistente actual. Si tipar correctamente requiere inferir cardinalidad, nullability, ownership o intención de dominio: **no inventar**, marcar `A_REVIEW` y derivar a FF-LOCAL-004.

# Evidencia requerida
Por modelo: path, clase, transformación, propiedades preservadas, ignores retirados y ambigüedades.

# Criterios de aceptación
- [ ] estilo SQLAlchemy 2.x consistente
- [ ] semántica persistente preservada
- [ ] sin cambios de integridad/negocio
- [ ] mapper/import smoke ejecutado
- [ ] pytest targeted cuando exista cobertura
- [ ] Ruff ejecutado
- [ ] type-check ejecutado si está disponible
- [ ] casos ambiguos listados para FF-LOCAL-004

# Validaciones
- mapper/import smoke: required
- pytest targeted: required cuando aplique
- Ruff: required
- type-check: required si disponible
- Alembic: no generar migraciones

# Impacto documental
Normalmente ninguno. Actualizar `current-state.md` sólo si cambia el estado real del Sprint 6.8.

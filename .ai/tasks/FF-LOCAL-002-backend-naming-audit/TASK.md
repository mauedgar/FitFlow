---
id: FF-LOCAL-002
title: Auditar convenciones de naming del backend
status: Ready
priority: High
area: backend
execution_lane: codex
type: audit
baseline_revision: pending
---

# Objetivo

Inventariar convenciones reales de nombres por capa y proponer una normalizacion consistente sin modificar archivos.

# Dependencia

Ejecutar despues de FF-LOCAL-001 o, como minimo, cuando exista un validation baseline suficiente para proteger una futura fase de renombres.

# Contexto minimo

Leer:
- `AGENTS.md`
- `docs/architecture.md`
- `docs/current-state.md`
- `docs/process/task-lifecycle-and-reporting.md`

# Scope

- `backend/app/routers/`
- `backend/app/schemas/`
- `backend/app/services/`
- `backend/app/crud/`
- `backend/app/db/models/`
- imports/referencias necesarias para medir impacto

# Fuera de scope

- no renombrar;
- no editar imports;
- no cambiar clases/metodos;
- no refactorizar arquitectura;
- no corregir estilo no relacionado.

# Evidencia requerida

Tabla:
`current_path | layer | observed_pattern | proposed_convention | violation? | rename_candidate | impact`

Distinguir convenciones validas por capa. Por ejemplo, un router plural (`bookings.py`) puede ser correcto aunque service/model sean singulares.

# Criterios de aceptacion

- [ ] todas las capas objetivo fueron inventariadas;
- [ ] se separa inconsistencia real de diferencia intencional entre capas;
- [ ] cada candidato de rename incluye referencias/impacto;
- [ ] no se modifico ningun archivo de produccion;
- [ ] ambiguedades se marcan `A revisar`;
- [ ] se propone una task separada de implementacion si corresponde.

# Validaciones esperadas

- git diff: debe estar limpio salvo artefactos de task permitidos
- pytest: N/A para auditoria read-only
- Ruff/type-check: N/A salvo que se ejecute solo como evidencia baseline

# Impacto documental esperado

- posible convencion en `AGENTS.md`/`architecture.md` solo despues de aprobacion humana

---
id: FF-LOCAL-005
title: Auditar y alinear enums y estados del dominio
status: Done
priority: High
area: backend
execution_lane: codex
type: refactor
baseline_revision: pending
---

# Objetivo

Inventariar los valores enumerados utilizados realmente por FitFlow,
reconciliarlos con el dominio aceptado y centralizar enums faltantes o
inconsistentes sin cambiar reglas de negocio arbitrariamente.

# Scope

- backend/app/schemas/enums.py
- backend/app/db/models/
- backend/app/schemas/
- backend/app/services/
- backend/app/crud/
- backend/app/routers/
- migraciones relevantes
- tests
- frontend solamente para detectar contratos/API dependientes

# Fase A — Auditoría read-only

Inventariar:

enum | value | definición | consumidores | persistencia | docs | estado

Buscar también strings hardcodeados correspondientes a:

- roles
- booking status
- membership status
- membership plan
- allowed plan
- session status
- difficulty
- activity type

# Casos explícitos a verificar

- ClassSessionStatus.draft
- AllowedPlan vs MembershipPlan
- ausencia intencional o no de gym_only en AllowedPlan
- valores persistidos por SQLAlchemy/PostgreSQL
- valores utilizados por frontend/API
- posibles estados definidos como strings fuera de enums

# Regla de decisión

No agregar, eliminar ni renombrar un valor solamente para hacer coincidir
documentación y código.

Clasificar cada caso como:

- CONFIRMED
- MISSING
- REDUNDANT
- LEGACY
- A_REVIEW

# Fase B — Implementación

Sólo después de la auditoría:

- agregar enums/valores inequívocamente necesarios;
- sustituir strings hardcodeados seguros;
- corregir documentación de enums;
- mantener compatibilidad de persistencia;
- no realizar migraciones destructivas sin aprobación.

# Criterios de aceptación

- [ ] inventario completo;
- [ ] no quedan estados relevantes descubiertos sin clasificación;
- [ ] ClassSessionStatus.draft queda resuelto;
- [ ] AllowedPlan queda conceptualmente definido;
- [ ] no se cambia semántica sin evidencia;
- [ ] tests relevantes agregados/actualizados;
- [ ] Ruff/type-check ejecutados;
- [ ] discrepancias restantes documentadas como A revisar.

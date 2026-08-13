---
id: <JIRA-KEY-or-local-id>
title: <titulo corto>
status: Ready
priority: <High|Medium|Low>
area: <backend|frontend|infra|docs|ai-tooling>
execution_lane: <human|codex|aider|mixed|undecided>
type: <feature|fix|refactor|audit|test|docs|tooling>
baseline_revision: <git-sha-or-pending>
---

# Objetivo

<resultado observable que se busca>

# Contexto minimo

<solo lo necesario para ejecutar; enlazar docs canonicos si aplica>

# Scope

- <archivo/directorio/concepto>

# Fuera de scope

- <cambios explicitamente excluidos>

# Restricciones

- no inventar arquitectura;
- no ampliar scope sin registrar la necesidad;
- <otras>

# Evidencia requerida

- <paths/simbolos/tests/diff/etc>

# Criterios de aceptacion

- [ ] <criterio 1>
- [ ] <criterio 2>

# Validaciones esperadas

- pytest: <targeted/full/N/A>
- ruff: <required/N/A>
- type-check: <required/N/A>
- alembic/openapi/frontend: <si aplica>

# Impacto documental esperado

- <none|current-state|architecture|domain|ADR|roadmap|quality|process>

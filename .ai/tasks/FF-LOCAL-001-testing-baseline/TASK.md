---
id: FF-LOCAL-001
title: Establecer baseline operativo de testing backend
status: Ready
priority: High
area: backend
execution_lane: codex
type: test
baseline_revision: pending
---

# Objetivo

Convertir la estructura pytest v3 en un harness realmente ejecutable contra el backend actual de FitFlow y agregar cobertura representativa de invariantes criticas.

# Contexto minimo

Leer:
- `AGENTS.md`
- `docs/current-state.md`
- `docs/quality-and-validation.md`
- `docs/adr/0009-backend-testing-baseline.md`

Inspeccionar el mecanismo real de dependencias/configuracion antes de modificarlo.

# Scope

- `backend/tests/`
- configuracion pytest/dev dependencies estrictamente necesaria;
- fixtures de test;
- wrappers de `scripts/quality/` si requieren ajuste;
- tests iniciales de un vertical slice critico, preferentemente Booking.

# Fuera de scope

- reescribir services/CRUD solo para facilitar tests;
- refactor general del backend;
- cambiar dominio;
- normalizar naming;
- introducir infraestructura de CI;
- implementar MCP.

# Restricciones

- primero diagnosticar como arranca el backend y como se obtiene AsyncSession;
- reutilizar configuracion existente cuando sea valida;
- tests deterministas y aislados;
- no usar DB productiva;
- no ocultar failures mediante mocks que eliminen la regla que se intenta probar.

# Evidencia requerida

- comando canonico de pytest reproducible;
- dependencias reconciliadas;
- fixtures documentadas;
- smoke harness real;
- al menos tests representativos para Booking/capacidad/duplicado o el primer punto critico viable;
- resultado de Ruff/type-check si estan disponibles.

# Criterios de aceptacion

- [ ] `python -m pytest backend/tests -m smoke` ejecuta correctamente.
- [ ] pytest-asyncio queda configurado cuando los tests async lo requieren.
- [ ] existe una estrategia de DB de test segura/aislada o el gap queda bloqueado explicitamente.
- [ ] al menos una regla real del dominio tiene test significativo, no solo `assert True`.
- [ ] los wrappers documentados coinciden con el entorno real.
- [ ] `RESULT.md` registra PASS/FAIL/UNAVAILABLE sin inferencias.
- [ ] ningun cambio funcional no relacionado fue introducido.

# Validaciones esperadas

- pytest smoke: required
- pytest targeted: required
- pytest broader: si la configuracion lo permite
- Ruff: required si disponible
- type-check: required si disponible
- Alembic: solo si se toca configuracion/modelos/migraciones

# Impacto documental esperado

- `docs/current-state.md`
- `docs/quality-and-validation.md`
- ADR 0009 solo si cambia la decision, no por completar implementacion

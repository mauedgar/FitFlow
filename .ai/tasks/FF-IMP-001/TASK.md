---
artifact: TASK
task_id: FF-IMP-001
title: Eliminar el ciclo de imports de schemas y restaurar startup/collection
status: PENDING_ACCEPTANCE
task_type: FIX
scope: backend
lane: ai_orchestrated
risk: medium
priority: P0
branch: fix/FF-IMP-001-schema-import-cycle
worktree: C:/Users/maued/orca/workspaces/FitFlow/fix-FF-IMP-001-schema-import-cycle
baseline: 5cfcd28b7c2aa0d0e871b72036bdfa4fe59e3827
depends_on: FF-AUD-001
ownership_keys:
  - path:.ai/tasks/FF-IMP-001/**
  - path:.ai/runs/FF-IMP-001-*/**
  - path:backend/app/schemas/class_schedule.py
  - path:backend/app/schemas/class_schedule_refs.py
  - path:backend/app/schemas/gym_class.py
  - path:backend/app/schemas/gym_class_refs.py
  - path:backend/tests/smoke/test_schema_startup.py
  - path:orca.yaml
  - config:orca-worktree-setup
---

# Objetivo

Eliminar el ciclo entre schemas Pydantic mediante registros `*_refs.py`, con
imports exclusivamente al inicio de cada modulo, preservando los nombres y
campos de los contratos publicos.

# Doc Sync de entrada

`FF-AUD-001` esta integrada en `develop` mediante `e71625c`, pero sus vistas
historicas aun indican `PENDING_ACCEPTANCE` y `NOT_INTEGRATED`. Esta diferencia
se registra aqui de forma append-only; no se reescribe evidencia previa ni se
infiere un timestamp de aceptacion.

# Alcance

- reestructurar las referencias cruzadas de ClassSchedule y GymClass;
- preservar imports publicos desde `app.schemas.class_schedule` y
  `app.schemas.gym_class`;
- agregar un smoke test de startup y generacion OpenAPI;
- incluir la copia de `backend/.env` en el setup Orca, autorizada expresamente
  por el Developer para este commit;
- producir evidencia v2 y detener el run en `PENDING_ACCEPTANCE`.

# Fuera de alcance

- DB, ORM, CRUD, services, routers y migraciones;
- reglas de dominio, enums y dependencias;
- frontend, contenido de secretos o `.env`, ADR y deuda no relacionada;
- aceptar, mergear o promover la task a `DONE`.

# Criterios de aceptacion

- [ ] AC-1: `from app.main import app` termina con exit code 0.
- [ ] AC-2: pytest completa collection sin errores de import circular.
- [ ] AC-3: contratos Pydantic, RRULE y Booking afectados se ejecutan.
- [ ] AC-4: `app.openapi()` genera el contrato en `fitflow-test`.
- [ ] AC-5: smoke, metadata ORM, Redis y allowed-plan siguen pasando.
- [ ] AC-6: Ruff, Pyright y `alembic heads` se ejecutan y registran.
- [ ] AC-7: no cambian DB, ORM, migraciones ni dominio.
- [ ] AC-8: Validator y Reviewer independientes producen evidencia.

# Documentos requeridos

- `AGENTS.md`;
- `docs/SOURCE_OF_TRUTH.md`;
- `docs/process/task-lifecycle-and-reporting.md`;
- `docs/process/risk-and-parallelism.md`;
- `docs/quality-and-validation.md`;
- artefactos `FF-AUD-001` declarados por el prompt de continuacion.

# FitFlow Baseline v3 - adopcion

Esta carpeta esta preparada para copiarse sobre el root de FitFlow.

## Antes de copiar

1. Tener un commit/checkpoint limpio.
2. No reemplazar el `.gitignore` real: fusionar `.gitignore.fitflow-v3-additions`.
3. Revisar si ya existe `.aiderignore`; el archivo v3 puede reemplazarlo solo si no contiene exclusiones adicionales necesarias.
4. Mantener secretos fuera del repositorio.

## Al copiar

Se agregan/actualizan:
- `AGENTS.md`
- `docs/`
- `.ai/`
- `.aiderignore`
- `.aiderignore.backend`
- `backend/pytest.ini`
- `backend/tests/`
- `scripts/quality/`

## Primera verificacion

Desde la raiz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_tests.ps1 -m smoke
```

El smoke minimo verifica el harness. No declara cobertura del dominio.

## Primeras tasks

1. `.ai/tasks/FF-LOCAL-001-testing-baseline/TASK.md`
2. `.ai/tasks/FF-LOCAL-002-backend-naming-audit/TASK.md`

Los IDs son provisionales hasta confirmar el project key real de Jira.

## Prompts para otros chats

- `.ai/prompts/CODEX_BASELINE_SETUP.prompt.md`
- `.ai/prompts/MCP_FUTURE_RESEARCH.prompt.md`

## Adopcion como Source of Truth

Una vez copiado y revisado el diff, hacer un commit de baseline documental/operativo. A partir de ese commit, `docs/SOURCE_OF_TRUTH.md` y `AGENTS.md` definen la entrada canonica. Los documentos de `docs/archive/` quedan fuera del contexto activo.

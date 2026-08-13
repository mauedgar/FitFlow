# Migracion documental - baseline v3

**Fecha:** 2026-08-13

## 1. Motivo

La version v2 separo correctamente source of truth, arquitectura, dominio, roadmap e IA. La v3 conserva esa base y agrega dos capacidades que ahora son parte del baseline operativo:

1. ciclo de tareas/reportes comun a humano, Codex y Aider;
2. validation baseline con pytest como prerequisito de automatizacion confiable.

## 2. Documentos v2 preservados conceptualmente

Sin cambio de decision:
- ADR 0001 Chakra UI;
- ADR 0003 Modular Monolith;
- ADR 0004 RRULE target;
- ADR 0005 Booking atomico;
- ADR 0006 Pydantic v2;
- ADR 0007 pipelines IA.

ADR 0002 Git sigue vigente y se complementa con ADR 0008.

## 3. Nuevos documentos

- `docs/process/task-lifecycle-and-reporting.md`
- `docs/adr/0008-task-lifecycle-and-execution-lanes.md`
- `docs/adr/0009-backend-testing-baseline.md`
- `docs/ai/codex-operating-guide.md`
- `docs/ai/mcp-future.md`
- `.ai/` con templates, tasks iniciales y prompts
- `backend/tests/` como baseline estructural
- wrappers de `scripts/quality/`

## 4. Cambios de enfoque

- Pytest deja de ser una herramienta "esperada" y pasa a ser un baseline critico que debe volverse realmente operativo.
- Jira queda definido como control plane humano del trabajo, sin automatizacion obligatoria.
- MCP se registra como estudio futuro, no dependencia actual.
- task/result/reporting deja de pertenecer solo a `docs/ai/` y pasa a `docs/process/`.

## 5. Material historico

Los documentos originales de Sprint 6.8, Sprint 7, roadmap IA v1 e indexador v1 siguen archivados y fuera del contexto activo por defecto.

El documento formal v2 se mueve a `archive/superseded/` cuando se adopta el documento formal v3.

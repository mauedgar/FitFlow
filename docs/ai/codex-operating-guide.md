# Codex - Guia de integracion con FitFlow

**Estado:** Baseline de configuracion; la configuracion concreta se valida en una sesion separada.

## 1. Principio

Codex consume `AGENTS.md` como guia durable y consulta docs por necesidad. No cargar toda la carpeta `docs/` en cada tarea.

Para cambios complejos:
1. leer TASK;
2. investigar;
3. usar Plan mode cuando convenga;
4. acordar scope;
5. implementar;
6. ejecutar validaciones;
7. producir RESULT.

## 2. Contexto recomendado

Siempre:
- task actual;
- `AGENTS.md`.

Bajo demanda:
- `current-state.md`;
- `architecture.md`;
- `domain.md`;
- ADR especifico;
- `quality-and-validation.md`;
- evidencia del Project Index/codigo.

Evitar por defecto:
- `docs/archive/`;
- logs/transcripts;
- `.venv*`;
- `node_modules`;
- `.ai/local`.

## 3. Testing

Los comandos canonicos se declaran en `AGENTS.md` y `quality-and-validation.md`. Si el harness falla por configuracion/dependencias, Codex debe reportarlo como gap, no inventar PASS.

## 4. Worktrees/branches

Para tareas paralelas o de riesgo, usar aislamiento Git. No abrir dos lanes de escritura sobre los mismos archivos.

## 5. Project Index

Cuando exista:
- usarlo para localizar;
- recibir candidatos/rangos;
- verificar archivos reales;
- editar solo despues de verificar.

## 6. Referencias oficiales

- AGENTS.md: https://developers.openai.com/codex/agent-configuration/agents-md
- Best practices: https://developers.openai.com/codex/learn/best-practices
- Worktrees: https://developers.openai.com/codex/environments/git-worktrees
- MCP: https://developers.openai.com/codex/mcp

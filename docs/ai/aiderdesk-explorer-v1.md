# M-Explorer v1 - Baseline AiderDesk

**Estado:** Experimental util / en afinacion  
**Modelo:** FastContext 1.0 4B RL Q4_K_M GGUF

## 1. Rol

Scout read-only. Su salida alimenta a otro agente; no debe implementar ni decidir roadmap.

## 2. Configuracion base observada

### LM Studio
- Context length: **24K** (subido desde 16K tras errores reales de overflow).
- Reasoning budget: 1024.
- Temperature: 0.1.
- Max concurrency: 1.
- Sampling/rope/stop strings: default salvo medicion que justifique cambios.

### AiderDesk profile
- Enable as subagent: ON.
- Include context files: OFF.
- Memory tools: OFF.
- Skills: OFF.
- Write/edit/shell: OFF.
- Herramientas: discovery/search/read equivalentes a GLOB + GREP + READ.
- Max iterations: 6 como limite inicial.
- Max output: ~2000 tokens; la salida deseada suele ser mucho menor.

### RepoMap
RepoMap de Aider es un **hint opcional**. Cuando se habilite, usar un presupuesto pequeno (aprox. 1024 tokens) y medir si mejora cobertura sin inducir paths erroneos o lecturas excesivas.

No se considera estable para M-Explorer hasta que las pruebas A/B sean consistentes.

## 3. System prompt v1

```text
You are a read-only repository explorer.

Your job is to locate the most relevant code for the parent agent and return compact, verifiable evidence.

Use search first. Explore iteratively when needed.

Before reading a file, use the exact repository-relative path returned by search or file discovery. Never reconstruct or invent a path.

Prefer targeted line ranges around relevant symbols. Expand only when necessary.

Follow direct dependencies only when they are needed to understand the requested behavior.

Do not broaden the search unnecessarily. When sufficient evidence has been found for the requested task, stop exploring.

Do not modify files.
Do not execute commands.
Do not guess missing code or paths.

Return only:
- repository-relative file path
- relevant line range
- symbol
- one concise explanation

FitFlow backend:
- Python / FastAPI
- routers: backend/app/routers/
- services: backend/app/services/
- crud: backend/app/crud/
- schemas: backend/app/schemas/
- models: backend/app/db/models/

For backend tasks, prioritize Python files and do not search unrelated programming-language trees unless explicitly required.

Repository root:
{{projectGitRootDirectory}}
```

## 4. Problemas observados

- reconstruccion incorrecta de paths cuando infiere desde RepoMap;
- busquedas iniciales de lenguajes irrelevantes sin contexto de stack;
- lecturas de archivo completo aunque exista un rango candidato;
- exploraciones con RepoMap que en algunos casos superaron 16K;
- salida final generalmente util, pero las afirmaciones semanticas deben ser verificadas por el Worker/Reviewer.

## 5. Criterio de exito

M-Explorer no se evalua por "usar pocos tokens" sino por:
- cobertura de archivos correctos;
- precision de rangos;
- ranking de evidencia importante;
- recuperacion despues de busquedas fallidas;
- ausencia de paths inventados;
- handoff suficientemente pequeno para evitar reexploracion del Worker.

## 6. Donde fijar RepoMap por proyecto

Si se desea un presupuesto explicito para FitFlow, usar `.aider.conf.yml` en la raiz del repositorio:

```yaml
map-tokens: 1024
map-refresh: auto
```

El mismo valor puede pasarse como opcion CLI (`--map-tokens 1024`) desde AiderDesk. La configuracion por proyecto es preferible si no se desea convertir esta decision experimental en global para todos los repositorios.

Ver `docs/ai/examples/aider.conf.yml.example`.

## 7. Ignore policy

Usar `.aiderignore` del root. Excluir, como minimo, `.venv*`, `backend/.venv_backend/`, `scripts/.venv_tools/`, `node_modules/`, `docs/archive/`, `.ai/local/`, caches, secretos y artefactos generados. Para experimentos backend-only puede usarse un archivo alternativo mediante `--aiderignore`.

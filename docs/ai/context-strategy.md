# Estrategia de contexto en capas

## 1. Objetivo

Reducir la cantidad de tokens que un agente potente gasta en exploracion repetida y, al mismo tiempo, evitar que un modelo local de menor capacidad decida la arquitectura del proyecto.

## 2. Capas

### L0 - TASK / Task prompt
Objetivo concreto, constraints y criterio de aceptacion.

### L1 - AGENTS.md
Instrucciones operativas durables: estructura, source of truth, limites de autonomia y comandos/validaciones de alto nivel.

### L2 - Docs canonicos
Solo los documentos relevantes para la tarea: current-state, architecture, domain, ADR especifico, quality.

### L3 - Contexto derivado reutilizable
Project Index, grafo, busqueda semantica, docstrings/pdoc y un resumen estructural neutral.

### L4 - Runtime hints
RepoMap de Aider, archivos abiertos, resultados de M-Explorer, grep/read live.

### L5 - Evidencia final
Codigo real/rangos leidos inmediatamente antes de implementar.

El Worker/Solver deberia recibir L0/L1 + documentos estrictamente necesarios + L5; no todo el historial de L3/L4.

## 3. Context Package neutral

Para reutilizar busquedas entre agentes sin acoplarse a AiderDesk:

```json
{
  "revision": "git-sha",
  "query": "...",
  "scope": ["backend"],
  "evidence": [
    {
      "path": "backend/app/services/booking_service.py",
      "symbol": "validate_no_overbooking",
      "start_line": 0,
      "end_line": 0,
      "reason": "capacity business rule",
      "source": "symbol|semantic|graph|textual"
    }
  ],
  "relations": [],
  "generated_at": "..."
}
```

Los rangos del ejemplo son placeholders: el paquete real siempre debe derivarlos del snapshot indexado.

## 4. RepoMap

Aider mantiene su RepoMap como contexto runtime y puede ser muy util para orientar un agente. No se considera una API de intercambio entre pipelines.

El Project Index puede generar una representacion **RepoMap-like** neutral (`repo_summary.json` o `repo_summary.md`) con simbolos/rutas/relaciones importantes. Esto permite que Codex, herramientas MCP u otros agentes reutilicen estructura sin depender del formato interno de Aider.

## 5. Docs e indice

Indexar por defecto:
- codigo propio;
- docs canonicos activos;
- ADRs activos;
- tests relevantes;
- configuracion no secreta.

Excluir por defecto:
- `docs/archive/`;
- `.venv*` y `backend/.venv_backend/`;
- `node_modules/`;
- `__pycache__/`;
- `.git/`;
- `.env*`, secretos, binarios y artefactos generados.

## 6. Regla de economia

El objetivo no es minimizar tokens del Explorer a cualquier costo. El objetivo es minimizar **exploracion repetida del Solver/Worker** manteniendo cobertura y evidencia. Un resultado corto y correcto que evita una exploracion mayor es una optimizacion aunque el explorer haya usado contexto local.

## 7. Contexto operativo de tasks

`TASK.md`, `PLAN.md` y `RESULT.md` son artefactos operativos compactos. Los transcripts completos y logs pertenecen a `.ai/local/` y no deben entrar al contexto normal.

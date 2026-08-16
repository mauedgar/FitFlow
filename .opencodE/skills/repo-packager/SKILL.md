---
name: repo-packager
description: Empaqueta contexto de repositorio con PageRank sobre el grafo de imports de Repomix. Úsala cuando necesites un pack reducido (overview), drill-down (mapa fino de una zona) o ampliado (código real de paths concretos). Nunca decide si el contexto alcanza; solo empaqueta lo que se le pide.
---

# Repo Packager

## Descripción

Empaqueta contexto de un repositorio para LLMs usando PageRank local sobre grafo de imports a partir de JSON de Repomix. Se activa con pedidos de contexto reducido, ampliado, drill-down, empaquetar repo, seleccionar archivos relevantes, reducir tokens de código, mapa de dependencias o pack de paths específicos. Entrega packs rankeados o código real sin decidir si son suficientes. El agente controla cuándo pedir cada modo.

## Overview

Skill que prepara packs de contexto de un repositorio. Calcula PageRank una vez sobre el grafo de dependencias (imports) generado a partir de la salida JSON de Repomix con `--compress`. Entrega tres tipos de pack bajo demanda del agente. Nunca decide si el contexto alcanza ni explora por su cuenta.

## Prerequisites

- `npx repomix` disponible (o el JSON ya generado).
- Python 3 + `networkx` instalado (`uv pip install networkx`).
- Archivo `.repomixignore` (y `.gitignore`) del repo se respetan automáticamente por Repomix; reducen ruido de tests, generated, etc.

## Invocation modes

Usa siempre el script `scripts/pack.py`. Los tres modos son:

### 1. reducido (default / overview)

```bash
python scripts/pack.py reducido \
  --json repo.json \
  --budget 8000 \
  [--personalize path1 path2 ...] \
  [--signatures-only]
```

- Calcula PageRank (reutiliza cache si existe).
- Selecciona archivos hasta el token-budget.
- Incluye lista de **candidatos a expansión** con score y razón corta.
- `--signatures-only` entrega solo firmas + imports (aún más ligero).

### 2. ampliado (código real completo)

```bash
python scripts/pack.py ampliado \
  --paths path1,path2,dir3 \
  [--json repo.json]
```

- Ejecuta Repomix **sin** `--compress` solo sobre los paths indicados.
- Límite duro: máximo 10 paths por llamada.
- Devuelve código fuente real listo para trabajar.

### 3. drill-down (mapa fino de una zona)

```bash
python scripts/pack.py drill-down \
  --json repo.json \
  --focus path/o/zona \
  --budget 6000 \
  [--signatures-only]
```

- Reutiliza el grafo global.
- Aplica personalización fuerte sobre el focus.
- Entrega un nuevo pack reducido + sus propios candidatos centrados en esa zona.

## Workflow esperado del agente

1. Generar o reutilizar el JSON base:
   ```bash
   npx repomix --style json --compress -o repo.json
   ```
2. Pedir **reducido** para obtener el mapa + candidatos.
3. Según necesidad:
   - Pedir **drill-down** de una zona para afinar el mapa.
   - Pedir **ampliado** de paths concretos (puede hacerse directamente, sin reducido previo).
4. El agente decide el siguiente paso. La skill solo empaqueta lo pedido.

## Output format

Todos los modos imprimen en stdout un bloque claro con:

- Metadata (modo, tokens estimados, archivos incluidos/excluidos).
- Lista de paths seleccionados + scores (cuando aplica).
- Lista de candidatos a expansión (reducido y drill-down).
- Contenido del pack.

El agente debe copiar/pegar o inyectar solo la sección de contenido que necesite.

## Cache y reutilización

- El grafo + ranking se guardan en `.repo-packager-cache/` junto al JSON.
- Drill-down y personalizaciones posteriores reutilizan el cache.
- Si el JSON cambia (mtime), se recalcula automáticamente.

## Limits and safeguards

- Ampliado: máximo 10 paths por invocación.
- Budget del reducido/drill-down es obligatorio y se respeta estrictamente.
- Ruido ya filtrado por `.repomixignore` del proyecto.
- Si se piden demasiados paths en ampliado, el script avisa del tamaño estimado y recorta a los 10 primeros.

## Script location

Todos los comandos se ejecutan desde la raíz del skill o indicando la ruta completa a `scripts/pack.py`.
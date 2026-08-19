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
- Python 3 + `networkx` ya disponible en un entorno verificado. No instalarlo
  como efecto lateral de una ejecución de contexto.
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
- El contrato vNext no permite truncado silencioso. Si se piden mas de 10 paths,
  la salida debe ser `PARTIAL` con `requested`, `included` y `omitted`, o
  `TOO_MANY_PATHS`. Hasta implementar `FF-AI-VNEXT-006`, cualquier recorte de la
  version actual se trata como `PARTIAL` y Explorer no puede asumir suficiencia.

## Estado vNext

La skill ya incluye un parche local para cerrar los gaps de exclusiones y
señalización de estado: se aplica filtro de `.repomixignore`/`.gitignore`, se
normalizan rutas Windows, se excluyen `.env` y cachés sensibles, y se devuelve
`PARTIAL`/`EMPTY` cuando el pack queda acotado por budget o límites.

Quedan pendientes las pruebas formales del baseline para cerrar la validación de
regresión: UTF-8 en Windows, matching de globs complejos, carga de exclusiones
provenientes de múltiples ignore files, selección scoped bajo presupuestos
pequeños y overflow de `ampliado` con más de 10 paths.
`scripts/.venv_tools` puede reutilizarse para discovery; no es el entorno
oficial de FitFlow-ai.

## Pruebas de regresión planificadas para baseline

1. Exclusiones de entorno y secretos: `.env`, `.env.*`, `node_modules`, `__pycache__`, caches, logs y `.repo-packager-cache`.
2. Integración de `.repomixignore` + `.gitignore` sin duplicar o reasignar patrones.
3. Rutas con separadores Windows (`\\`) y prefijos `./`.
4. `reducido`/`drill-down` con budget pequeño que deba devolver `PARTIAL` en lugar de truncar silenciosamente.
5. `ampliado` con >10 paths: status `PARTIAL`, `requested`, `included` y `omitted` visibles.
6. Focus scoped: archivos dentro del focus debieran priorizarse sin romper el ranking global.
7. Smoke end-to-end con `repo.json` real usando `.venv_tools` para evitar dependencia del entorno del sistema.

## Script location

Todos los comandos se ejecutan desde la raíz del skill o indicando la ruta completa a `scripts/pack.py`.

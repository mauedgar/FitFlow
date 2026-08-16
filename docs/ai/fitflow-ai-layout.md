---
document_id: FF-AI-LAYOUT-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Layout de FitFlow-ai

Ruta recomendada:

```text
C:\Proyectos Web\
  FitFlow\
  FitFlow-ai\
```

La separación exacta “milimétrica” no es necesaria, pero ambos repositorios
deben ser hermanos para evitar anidar entornos, índices y dependencias dentro
del producto.

```text
FitFlow-ai/
  docs/                 # arquitectura del tooling
  config/               # perfiles sin secretos
  scripts/              # CLI/hooks
  src/                  # adapters, parsing, ingestion, retrieval
  tests/                # unit/integration/evals
  data/
    staging/            # entradas temporales normalizadas
    derived/            # inventarios, XML y manifests regenerables
  storage/              # estado local de Qdrant/cache; ignorado
  exports/              # bundles/reportes entregables; ignorado por defecto
  logs/                 # trazas locales; ignorado
```

## Semántica de datos

- `data/staging`: material transitorio de una ejecución; puede borrarse y
  regenerarse.
- `data/derived`: outputs deterministas con manifest; no son verdad canónica.
- `storage`: persistencia técnica local y volúmenes.
- `exports`: paquetes explícitos para intercambio o auditoría.

`env_tools` puede vivir en `FitFlow-ai` como entorno local ignorado. El entorno
`backend/.venv_backend` permanece propiedad de FitFlow y no debe reutilizarse
para indexación.

---
document_id: FF-PROCESS-IGNORE-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-16
---

# Política de exclusión

## Contexto e indexación

Excluir siempre:

```text
.git/
.venv*/
backend/.venv_backend/
node_modules/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
coverage/
docs/archive/
.ai/local/
data/staging/
storage/
exports/
logs/
.env
.env.*
*.key
*.pem
*.p12
*.sqlite*
```

Aplicar allowlist adicional para docs: solo `machine_context: true`. Los tests y
config no secreta se incluyen según scope.

## Versionado

Versionar:

- docs canónicos, ADR, prompts, config sin secretos, schemas, templates, tareas
  y fixtures pequeños;
- manifests que permitan reproducir una ejecución cuando sean útiles.

Ignorar:

- vectores, DB/volúmenes Qdrant, modelos descargados, caches, logs, traces,
  snapshots grandes y exports regenerables.

## Bundles

Un bundle de intercambio puede incluir outputs ignorados, pero vive en
`exports/`, registra hashes y nunca se convierte en fuente canónica por estar
adjunto a una tarea.

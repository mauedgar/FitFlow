---
document_id: FF-AI-PIPELINE-INDEX-001
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Pipeline de indexación y recuperación

## Objetivo

Mantener contexto derivado reproducible para `backend`, `frontend` y `mixed`,
con cambios incrementales y borrados correctos.

## Etapas

1. **Discover:** aplicar scope y exclusiones; generar inventario limpio.
2. **Structure:** extraer clases, símbolos, imports y relaciones con Repomix/repo-packager;
   mientras no exista, producir XML de relaciones mediante el generador actual (`xml_generator`).
3. **Snapshot:** ejecutar Repomix con perfil del scope.
4. **Normalize:** LlamaIndex transforma archivos y docs permitidos en documentos
   y nodos con metadata común.
5. **Embed:** EmbeddingGemma-300M genera vectores por lotes.
6. **Upsert/Delete:** Qdrant refleja nodos vigentes y elimina IDs ausentes.
7. **Verify:** hashes, conteos, filtros, consultas smoke y staleness.
8. **Promote:** publicar el índice como baseline aceptado después de review y
   validación.

## Fuentes incluidas

- código propio backend/frontend;
- tests;
- configuración no secreta;
- docs canónicos con `machine_context: true`;
- ADR aceptados relevantes.

Exclusiones: `.git`, `.venv*`, `backend/.venv_backend`, `node_modules`, caches,
build/dist, `.env*`, secretos, binarios, `docs/archive`, `.ai/local`, outputs,
staging y exports.

## Metadata mínima por nodo

```yaml
repository: FitFlow
scope: backend
baseline_revision: <git-sha-or-NO_COMMIT>
working_tree_fingerprint: <sha256>
path: backend/app/services/example.py
language: python
node_type: symbol
symbol: example
start_line: 1
end_line: 20
content_hash: <sha256>
parser_version: <version>
embedding_model: EmbeddingGemma-300M
machine_context: true
```

El tamaño/dimensión de la colección se deriva del modelo cargado y se valida en
runtime; no se codifica por memoria.

## Identidad

`node_id = sha256(repository | path | node_type | symbol | structural_anchor)`.
El contenido no forma parte del ID para permitir upsert estable; sí forma parte
de `content_hash`. Renames se modelan como delete + insert salvo detector
explícito.

## Triggers

- creación, cambio o borrado marca rutas `dirty`;
- no reindexar en cada tecla/save;
- después de targeted validation y review `PASS`: `index sync --dirty`;
- después de aceptación humana: `index promote`;
- cambios de parser, chunker, embedding o exclusiones fuerzan rebuild versionado.

Si no existe commit, usar `baseline_revision: NO_COMMIT` más fingerprint del
working tree. Un índice de trabajo no sustituye al índice promovido.

## Recuperación

Aplicar primero filtros por repositorio, scope, revisión, path/language/tipo y
`machine_context`. Combinar evidencia estructural, textual y vectorial. El
Explorer verifica los rangos en archivos reales antes de emitir el package.

## Evaluación

Set inicial de 15–20 consultas con respuesta esperada y archivos/símbolos
relevantes. Medir recall útil, precisión en top-k, cobertura de citas, staleness,
latencia, tokens entregados y tasa de solicitud de contexto adicional.

## Fallos

- parser falla: marcar archivo `UNPARSED`, usar fallback por archivo y no ocultar;
- embedding falla: conservar estructura/texto, no promover vector incompleto;
- Qdrant no disponible: `UNAVAILABLE`, sin índice falso;
- borrado incompleto o hash inconsistente: `FAIL` y rebuild acotado;
- metadata sin revisión/fingerprint: rechazar ingesta.

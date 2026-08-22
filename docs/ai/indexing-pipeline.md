---
document_id: FF-AI-PIPELINE-INDEX-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/indexing-pipeline.md
---

# Retrieval semantico posterior

## Gate de entrada

No implementar embeddings hasta que docs vNext, contracts, registries,
ContextPackager, Explorer y golden queries sean estables y medidos.

## Primer uso

Retrieval agrega candidatos al Explorer. No participa en routing critico,
autoridad documental ni edicion automatica.

## Arquitectura provisional

LlamaIndex TypeScript puede implementar ingestion/retrieval detras de un port.
Qdrant y el embedding se seleccionan despues de una evaluacion reproducible.
Version, corpus, baseline, excludes hash y embedding ID forman la identidad.

## Promocion

Requiere recall/precision acordados, cero critical misses del golden set,
deletes/renames correctos, stale detection, rollback y costo aceptable. Hasta
entonces la feature flag permanece disabled.

---
document_id: FF-ADR-0012
status: superseded
machine_context: true
superseded_by: FF-ADR-0015
---

# ADR 0012: Contexto estructural y vectorial

- **Estado:** Superseded por ADR 0015
- **Fecha:** 2026-08-16

## Contexto

Los agentes necesitan orientación estructural y recuperación semántica sin
cargar el repositorio completo ni depender de un proveedor externo para crear
un mapa.

## Decisión

La capa de contexto derivado usa:

1. inventarios depurados `estructura_Directorios<scope>.txt`;
2. grafo `estructura_de_clases_<YYYY-MM-DD>.xml`;
3. bundles Repomix por scope;
4. Repomix/repo-packager para símbolos, imports y relaciones;
5. LlamaIndex para ingesta/recuperación;
6. Qdrant como vector store;
7. EmbeddingGemma-300M como embedding inicial.

Hasta que Repomix/repo-packager esté completo en cobertura, los inventarios,
XML de relaciones y búsqueda directa cubren la orientación estructural.
Fallback: `xml_generator` produce `estructura_de_clases_<fecha>.xml` mientras
el grafo Repomix se consolida. Ningún artefacto derivado supera a
código/tests/config/migraciones.

RepoMap queda descartado. La plataforma no usa OpenRouter para producir
estructura ni contexto.

## Identidad e incrementalidad

Cada nodo usa un ID determinista basado en repositorio, revisión/fingerprint,
ruta, tipo, símbolo y rango estable. Un cambio crea upsert; una eliminación
debe retirar los nodos correspondientes. La promoción se realiza después de
validación y revisión aceptadas.

## Gate

La adopción requiere compatibilidad confirmada, regeneración reproducible,
filtros por metadata y 15–20 consultas doradas con métricas de cobertura,
precisión útil, latencia y tamaño de contexto.

## Consecuencias

El sistema puede entregar contexto acotado y trazable. A cambio, debe controlar
staleness, borrados, colisiones, exclusiones y versiones de embedding.

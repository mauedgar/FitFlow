---
document_id: FF-ADR-0015
status: accepted_pending_implementation
machine_context: true
version: 1.1
updated: 2026-08-21
supersedes: [FF-ADR-0012]
---

# ADR 0015: Empaquetado determinista y retrieval diferido

## Contexto

La baseline v4 juntaba inventario, AST, Repomix, LlamaIndex, Qdrant y embedding
en una secuencia temprana. `repo-packager` ya cubre empaquetado y PageRank, pero
no debe actuar como Explorer.

## Decision

Explorer decide necesidad y emite `ContextRequest`. `repo-packager` implementa
`ContextPackagerPort` con modos `reduced`, `drill_down` y `expanded`; no decide
suficiencia, no conserva Run State y no trunca silenciosamente.

La lectura directa de fuente real es obligatoria para editar o aprobar.
LlamaIndex, Qdrant y embeddings quedan feature-flagged hasta estabilizar
contratos, exclusions, lineage y golden evals.

## Consecuencias

Las correcciones funcionales de `repo-packager` fueron integradas en FitFlow-ai
mediante PR #2. La conformance con `ContextPackagerPort` permanece pendiente en
`FF-AI-VNEXT-006`. El grafo XML y los inventarios existentes son hints
historicos, no requisitos fijos de vNext.

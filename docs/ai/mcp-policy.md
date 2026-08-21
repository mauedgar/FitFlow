---
document_id: FF-AI-MCP-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/implementation-roadmap.md
---

# Politica MCP

MCP no forma parte del MVP. Solo puede habilitarse despues de estabilizar ports,
authz local, schemas, context retrieval, observabilidad y red-team.

La primera superficie sera local, read-only y allowlisted. No expone escritura,
shell, secretos, promotion, Git o acceso remoto. La disponibilidad de MCP en un
runtime no justifica su adopcion.

Toda tool requiere schema compacto, timeout, limites, audit event y prueba de
prompt/tool poisoning. Las capacidades de escritura exigen ADR independiente.

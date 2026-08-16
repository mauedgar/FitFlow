---
document_id: FF-MIGRATION-004
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Migración documental v3 -> v4

## Objetivo

Adoptar una única arquitectura de agentes, retirar decisiones operativas
reemplazadas y conservar trazabilidad histórica.

Aider y RepoMap quedan descartados. No instalar, configurar ni invocar
OpenRouter para reemplazarlos. Repomix cubre estructura y Codebase cubre
orquestación.

## Acciones

1. Reemplazar los documentos canónicos incluidos en este bundle.
2. Conservar ADR 0001–0010; cambiar 0007 a `Superseded` y 0008 a `Amended`.
3. Añadir ADR 0011–0013.
4. Mover guías operativas reemplazadas a `docs/archive/superseded/ai-v3/` o
   retirarlas del índice; no cargarlas como contexto.
5. Adoptar `.ai/config`, prompts, contratos y plantillas v1.
6. Ejecutar `FF-AI-000` antes de tocar el entorno.
7. Crear `C:\Proyectos Web\FitFlow-ai` como repositorio hermano.

## Documentos retirados del conjunto activo

- `docs/ai/aiderdesk-explorer-v1.md`;
- `docs/ai/codex-operating-guide.md`;
- `docs/ai/development-pipelines.md`;
- `docs/ai/indexer-pipeline.md`.

Su contenido histórico no gobierna Codebase, roles, modelos ni fuentes de
contexto v4.

## Compatibilidad

No actualizar Python, pytest, Pylint, Ruff, Pyright, LlamaIndex, Qdrant,
Repomix u otra dependencia durante la migración documental. `FF-AI-000`
debe inventariar versiones, resolver restricciones y proponer una actualización
separada si fuera necesaria.

Pylint no se incorpora como gate canónico salvo decisión posterior: el baseline
confirmado usa Ruff y Pyright.

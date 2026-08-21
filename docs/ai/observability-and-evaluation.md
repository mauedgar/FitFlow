---
document_id: FF-AI-OBS-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/implementation-roadmap.md
---

# Observabilidad y evaluacion

## MVP

Run events y usage records forman un ledger append-only. Un Workflow Observer
local muestra estado, ruta, context lineage, gates, modelos, tokens, retries y
FinOps summary. No requiere una plataforma SaaS.

## Privacidad

No registrar secretos, prompts completos innecesarios ni contenido sensible.
Preferir hashes, paths, contadores y referencias a artefactos locales.

## Evals

- conformance de schemas y transitions;
- fixtures de Router y Model Resolver;
- suficiencia/exclusion/staleness de contexto;
- defects sembrados para Reviewer;
- first-pass acceptance y retrabajo por rol/modelo;
- golden queries antes de retrieval semantico.

Braintrust, Phoenix y Promptfoo permanecen evaluables detras de adapters. No se
incorpora ninguno antes de disponer de runs, golden set y necesidad demostrada.

---
document_id: FF-AI-CONTEXT-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/current-state.md
---

# Estrategia de contexto

## Objetivo

Entregar evidencia minima suficiente, fresca y trazable sin convertir el
empaquetado o retrieval en autoridad.

## Responsabilidades

- el rol consumidor declara su necesidad;
- Explorer formula `ContextRequest` y decide suficiencia;
- `repo-packager` ejecuta un modo y devuelve resultado;
- Run State conserva lineage, destinatario, tokens y expansiones;
- Coder y Reviewer abren la fuente real antes de decidir.

## Modos

| Modo | Salida | Uso |
| --- | --- | --- |
| `reduced` | mapa PageRank, firmas, candidatos y scores | overview |
| `drill_down` | mapa centrado en una zona | comprender modulo |
| `expanded` | codigo real de paths explicitos | implementar/revisar |

Explorer puede pedir cualquier modo directamente. `expanded` no trunca en
silencio: devuelve `PARTIAL` y `omitted_paths` o `TOO_MANY_PATHS`.

## Presupuesto

Los valores de `.ai/config/scopes.yaml` son limites iniciales, no objetivos
de consumo. Cada entrega registra tokens estimados, hash, paths y destinatario.
Un override requiere motivo y queda en Run State.

## Perfiles por consumidor

Tests pueden omitirse en `reduced:implementation`, pero no por regla global.
Explorer selecciona `implementation`, `review`, `test` o un perfil explicito.

## Frescura

Un cambio de baseline o fingerprint invalida el package. La revalidacion puede
usar delta de paths; si la evidencia afectada no puede determinarse, regenerar.
Embeddings e indices solo producen candidatos y permanecen feature-flagged.

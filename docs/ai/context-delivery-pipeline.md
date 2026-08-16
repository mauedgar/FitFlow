---
document_id: FF-AI-PIPELINE-CONTEXT-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Pipeline de entrega de contexto

## Entrada

`CONTEXT_REQUEST` válido con task, pregunta, scope, baseline/fingerprint,
evidence types y presupuesto.

## Perfiles

| Scope solicitado | Inventario | Raíces | Budget |
| --- | --- | --- | ---: |
| backend | `estructura_Directoriosbackend.txt` | `backend/` | 8.000 |
| frontend | `estructura_Directoriosfrontend.txt` | `frontend/` | 8.000 |
| mixed | `estructura_Directoriostotal.txt` | backend + frontend + docs allowlist | 12.000 |

`docs_tooling` reutiliza inventario total con allowlist y 4.000 tokens.

## Etapas

1. **Classify:** confirmar que la pregunta coincide con el scope.
2. **Freshness:** comparar revisión/fingerprint de artefactos.
3. **Orient:** inventario y XML/Repomix.
4. **Retrieve:** Repomix/texto/vector con filtros.
5. **Verify:** abrir código/tests y confirmar rangos/hash.
6. **Reduce:** deduplicar, priorizar y aplicar budget.
7. **Serialize:** validar Context Package.
8. **Deliver:** entregar solo package + documentos allowlisted.

## Suficiencia

El package contiene definición/caso de uso, dependencias necesarias, tests y
contrato/doctrina afectados. Si no alcanza, declarar `gaps`; no compensar con
archivos irrelevantes.

## Fallos

- artefacto stale/invalid: regenerar o bloquear;
- Qdrant unavailable: usar estructura/texto y marcar `PARTIAL`;
- parser parcial: incluir warning y lectura directa;
- presupuesto insuficiente: Planner recorta o una persona autoriza override;
- dos rondas sin suficiencia: volver a PLAN.

---
document_id: FF-ADR-0017
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-18
supersedes: [FF-ADR-0013]
---

# ADR 0017: Run ledger, FinOps-as-Code y observer local

## Decision

Persistir artefactos v2 y eventos append-only por run. Usar SQLite local como
checkpoint/proyeccion regenerable. Implementar un Workflow Observer local antes
de adoptar una plataforma externa de trazas.

FinOps es policy-as-code: presupuesto incremental `USD 0`, pool pago disabled,
quality/risk gates antes de costo y escalamiento por evidencia. Registrar uso,
contexto, retries, latencia, cuota e intervenciones del desarrollador.

## Consecuencias

Phoenix deja de ser la eleccion inicial obligatoria. Phoenix, Braintrust y
Promptfoo pueden evaluarse mas tarde detras de ports, cuando existan runs y un
golden set. El optimizador automatico permanece disabled.

---
document_id: FF-AI-FINOPS-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-18
---

# FinOps-as-Code

## Politica

FinOps es una policy del workflow, no un agente. El presupuesto incremental es
`USD 0`. El pool `paid` esta disabled. Una excepcion requiere decision del
desarrollador, limite, expiracion y evidencia.

## Orden de decision

1. Cumplir criticality ceiling, privacidad y calidad minima.
2. Preferir funcion determinista cuando resuelve el paso.
3. Elegir recurso suficiente de menor costo total esperado.
4. Considerar quota, tokens, contexto, latencia, retries y retrabajo.
5. Escalar por evidencia de insuficiencia, no por preferencia de modelo.

## Pools

`deterministic`, `local`, `zen_included`, `openrouter_free`, `cloud_included` y
`paid_disabled`. Los pools gratuitos o experimentales tienen criticality
ceiling bajo hasta benchmark reproducible.

`copilot_included` esta disabled/deferred: no es un recurso invocable por AI
Core. Cualquier uso requiere que el desarrollador transmita manualmente la
orden y registre el resultado como intervencion externa.

## Metricas

`TokensPerAcceptedTask`, `ContextTokens`, `Attempts`, `FirstPassAcceptance`,
`EscalationRate`, `ContextReuse`, `DeveloperInterventions` y `Latency`.

El optimizador automatico permanece disabled. Los cambios de policy se proponen
con reportes y se aceptan por el desarrollador.

---
document_id: FF-MILESTONE-M4-001
status: planned
machine_context: true
program: FF-PROGRAM-POST-REBASELINE-001
post_m1_baseline: f152b8336245b01da1cea75da81b5a3c4e1a8420
---

# M4 - Staging and beta readiness

## Macro goal

Preparar el MVP estabilizado para una beta controlada y observable.

## Prioridad y evidencias del corte 2026-11-01

El Developer/Control selecciono M4 como **prioridad para preparar y calificar**
la beta, conservando el estado documental `planned` hasta demostrar su criterio
de cierre. Referencia operativa: [Issue #40](https://github.com/mauedgar/FitFlow/issues/40).
La rama `develop@24dc1f40afcee9bf5be5881af449fb123fe3b033` y el tree
`403843fd533a876f02af622d234971d6d741b116` son el baseline observado
para planificar, no certificacion runtime de staging.

Reutilizar los contratos vigentes de `docs/operations/`, incluidos los
procedimientos R005/R006 y el gate R007; no recomenzar implementaciones ya
existentes ni transferirles un PASS historico. El R007 solo puede decidir
`READY_FOR_BETA_DECISION` o `NOT_READY_FOR_BETA_DECISION` con evidencia exacta.
El despliegue externo y el lanzamiento quedan sujetos a decisiones Developer
separadas. Las deudas #25, #36, #37 se mantienen sin falsos cierres; el slice
funcional #38 es independiente. M5/Billing sigue diferido.

## Precondiciones

- M1 cerrado: cumplido.
- M2 cerrado.
- M3 cerrado o con excepciones explicitamente aceptadas.

## Trabajo agrupado

- entorno reproducible de staging;
- configuracion y secretos por entorno;
- logging y observabilidad basica;
- health/readiness checks;
- procedimiento de despliegue y rollback;
- smoke del vertical MVP en staging;
- criterios de beta controlada.

## Criterio de cierre

El producto puede desplegarse, observarse y validar su vertical MVP en staging
sin usar estado de desarrollo como dependencia oculta.

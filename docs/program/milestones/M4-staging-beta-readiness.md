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

---
document_id: FF-MILESTONE-M2-001
status: eligible_not_selected
machine_context: true
program: FF-PROGRAM-POST-REBASELINE-001
post_m1_baseline: f152b8336245b01da1cea75da81b5a3c4e1a8420
---

# M2 - API and async boundary hardening

## Macro goal

Endurecer la superficie HTTP/async del backend ya funcional con contratos y
tests reproducibles, sin mezclar cambios de dominio.

## Trabajo reconciliado

- cobertura API integral por recursos y auth;
- fixtures HTTP async compartidas con lifecycle controlado;
- residual de FF-FOLLOW-05 para Teacher/ClassSchedule;
- FF-FOLLOW-11: loaders explicitos, MissingGreenlet y N+1;
- mapeo consistente de errores de dominio a HTTP;
- regresiones Booking/Session/Membership/Auth;
- concurrencia donde exista una invariante real;
- refactors de fronteras heredadas solo cuando evidencia actual los justifique.

## Inputs post-M1

- `NB-R001-001`: revisar el costo y scope de `include_relations` que sobrecarga
  `class_sessions`.
- `NB-DEFERRED-001`: revisar rutas publicas alternativas de ClassSchedule con
  riesgo latente de relation loading.
- `NB-DEFERRED-002`: reconciliar vocabulario frontend `TRAINER` con backend
  `teacher` cuando corresponda al boundary contractual.

## Precondicion de runtime

El tooling de test pertenece al contrato declarado del proyecto y debe
materializarse reproduciblemente mediante `uv` en `backend/.venv`.

`.venv_backend` no es fuente autoritativa del contrato de dependencias.

## Exclusiones

- cambios de dominio;
- Membership 1:N;
- staging;
- limpieza global de estilo;
- reapertura de M1.

## Estado

`ELIGIBLE_NOT_SELECTED`

Este documento no autoriza ni inicializa un Product TaskCycle.

## Criterio de cierre

La cobertura HTTP relevante puede ejecutarse reproduciblemente y las fronteras
async no dependen de cargas implicitas no controladas.

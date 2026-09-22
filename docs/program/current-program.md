---
document_id: FF-PROGRAM-POST-REBASELINE-001
status: canonical_post_m1
machine_context: true
version: 1.1
baseline_commit: f152b8336245b01da1cea75da81b5a3c4e1a8420
baseline_tree: de30558227849afed1f24ef548b6eb29d73ecdad
reconciled: 2026-09-22
---

# Programa actual de FitFlow

## Proposito

Este documento mantiene el programa accionable de FitFlow despues del cierre
publicado de M1. `docs/roadmap.md` conserva las prioridades macro; este programa
organiza milestones ejecutables sin reabrir responsabilidades ya cerradas.

El repositorio es la fuente primaria. Los TASK historicos, runs, conversaciones
y artefactos locales son evidencia subordinada al baseline vigente.

## Baseline post-M1 confirmado

- `develop` publicado en `f152b8336245b01da1cea75da81b5a3c4e1a8420`.
- tree publicado `de30558227849afed1f24ef548b6eb29d73ecdad`.
- `FITFLOW-M1-OPERATIONAL-MVP-CERTIFICATION`:
  `ACCEPTED_INTEGRATED_AND_REMOTELY_PUBLISHED`.
- M1 no se reabre por findings no bloqueantes.
- El browser E2E no quedo establecido y no fue blocker de M1.
- El runtime local canonico usa `backend/.venv` y Python 3.11.3.
- `uv` es el dependency manager primario para materializacion reproducible.
- `pip` queda como herramienta diagnostica cuando resulte util.

## Cierre de M1

TaskCycle cerrado:

`CURRENT-FITFLOW-M1-OPERATIONAL-VERTICAL-CERTIFICATION-001`

Estado de producto:

`ACCEPTED_INTEGRATED_AND_REMOTELY_PUBLISHED`

Findings no bloqueantes preservados como inputs futuros:

| Finding | Clasificacion post-M1 |
| --- | --- |
| NB-R001-001 - `include_relations` sobrecarga `class_sessions` | M2 input |
| NB-DEFERRED-001 - rutas publicas alternativas de ClassSchedule conservan hazard latente de relation loading | M2 input |
| NB-DEFERRED-002 - vocabulario frontend `TRAINER` diverge de backend `teacher` | M2 input |

Estos findings no reabren M1 y no constituyen por si mismos autorizacion para M2.

## Contrato local de dependencias

- `pyproject.toml` y `uv.lock` son la superficie declarada.
- dependencias de test deben estar declaradas en `[dependency-groups].dev`.
- `backend/.venv` es el entorno local canonico.
- `.venv_backend` queda preservado hasta una decision posterior de retiro.
- no se copian dependencias accidentales desde entornos legacy.
- upgrades de Python requieren una responsabilidad separada.

## Milestones

1. **M1 - Operational MVP certification and minimal completion**
   - estado: `CLOSED`;
   - producto: `ACCEPTED_INTEGRATED_AND_REMOTELY_PUBLISHED`.

2. **M2 - API and async boundary hardening**
   - estado: `ELIGIBLE_NOT_SELECTED`;
   - incluye deuda API/async previamente reconciliada y findings post-M1;
   - requiere seleccion y autorizacion separadas.

3. **M3 - Persistence and configuration stability**
   - estado: `PLANNED`.

4. **M4 - Staging / beta readiness**
   - estado: `PLANNED`;
   - depende del cierre competente de M2 y M3 o excepciones explicitas.

5. **M5 - Post-MVP domain growth**
   - estado: `DEFERRED_POST_MVP`.

## Seleccion de siguiente responsabilidad

Este documento no selecciona M2 ni crea un nuevo Product TaskCycle.

La siguiente responsabilidad de desarrollo debe seleccionarse en
`ADV-FITFLOW-DEVELOPMENT` despues de reconciliar la materializacion post-M1 y,
si corresponde, publicar este estado programatico/contractual mediante un gate
separado.

## Reconciliacion posterior a cada milestone

Al cerrar cada milestone:

- confirmar logro del objetivo macro;
- reexaminar deuda deferred ahora elegible;
- incorporar trabajo nuevo descubierto;
- retirar o marcar elementos superseded;
- reconsiderar orden, particion o combinacion de milestones;
- preservar evidencia de proceso sin convertirla silenciosamente en autoridad
  de producto.

---
document_id: FF-PROGRAM-POST-REBASELINE-001
status: canonical_post_m2
machine_context: true
version: 1.2
baseline_commit: 60903101384713f8b1c51d18644ac134fab8f87c
baseline_tree: 580a13d9a8f4dd14ea3b52cc605552e7f2ff47c5
reconciled: 2026-09-28
---

# Programa actual de FitFlow

## Proposito

Este documento mantiene el programa accionable de FitFlow despues del cierre
competente de M2. `docs/roadmap.md` conserva las prioridades macro; este programa
organiza milestones ejecutables sin reabrir responsabilidades ya cerradas.

El repositorio es la fuente primaria. Los TASK historicos, runs, conversaciones
y artefactos locales son evidencia subordinada al baseline vigente.

## Baseline post-M2 confirmado

- `develop` publicado en `60903101384713f8b1c51d18644ac134fab8f87c`.
- tree publicado `580a13d9a8f4dd14ea3b52cc605552e7f2ff47c5`.
- M1 permanece `CLOSED`.
- M2 queda `CLOSED`.
- `Product_implementation_frontier` de M2:
  `COMPLETE_FOR_CURRENT_M2_SCOPE`.
- R001-R009 permanecen cerrados.
- no existe evidencia actual que requiera iniciar R010.
- M3 permanece planificado pero `NOT_SELECTED`; su implementacion no fue iniciada.
- el runtime local canonico usa `backend/.venv` y Python 3.11.
- `uv` permanece como dependency manager primario para materializacion reproducible.

## Cierre de M1

M1 permanece cerrado. Su cierre no se reabre por el cierre de M2 ni por findings
diferidos no bloqueantes.

## Cierre de M2

Milestone:

`M2 - API and async boundary hardening`

Estado:

`CLOSED`

Baseline terminal de Product:

`60903101384713f8b1c51d18644ac134fab8f87c`

La secuencia R001-R009 es terminal y forma el frente de implementacion M2
aceptado. La verificacion final fresca del baseline integrado demostro:

- correspondencia exacta local/remoto sobre `develop`;
- worktree limpio;
- `fitflow_test` como base efectiva de test;
- Alembic en el unico head `e4f5a6b7c8d9`;
- regresion backend completa: `110 passed`;
- contratos HTTP M2 dirigidos: `52 passed`.

La cobertura demostrada es suficiente para el scope M2 actual. Esto no afirma
cobertura combinatoria exhaustiva de todas las rutas HTTP ni ausencia global de
N+1.

## Evidencia diferida preservada

| Finding | Disposicion al cierre M2 |
| --- | --- |
| contratos HTTP directos restantes con cobertura dispersa | `DEFERRED_NON_BLOCKING` |
| evaluacion global de N+1 | `DEFERRED_NON_BLOCKING` |
| lifecycle HTTP de aplicacion controlado de forma global | `DEFERRED_NON_BLOCKING` |
| `NB-DEFERRED-002` - frontend `TRAINER` vs backend `teacher` | `DEFERRED_NON_BLOCKING` |

La frontera publica de ClassSchedule si tiene evidencia concreta de loader
explicito y conteo acotado de queries; esa evidencia no se generaliza a una
afirmacion global de ausencia de N+1.

Invariante de gobierno:

`finding != decision != authorization`

Ningun finding diferido autoriza automaticamente trabajo adicional ni crea R010.

## R009

El cierre de R009 se preserva como hecho de Product:

```yaml
R009_Phase_2B:
  closure_mode:
    FITFLOW_NATIVE_RECONCILIATION
```

No se atribuye ese cierre a Tecnotron Recipe B.

## Milestones

1. **M1 - Operational MVP certification and minimal completion**
   - estado: `CLOSED`.

2. **M2 - API and async boundary hardening**
   - estado: `CLOSED`;
   - Product implementation frontier: `COMPLETE_FOR_CURRENT_M2_SCOPE`;
   - baseline terminal: `60903101384713f8b1c51d18644ac134fab8f87c`.

3. **M3 - Persistence and configuration stability**
   - estado: `PLANNED / NOT_SELECTED`;
   - baseline post-M2 disponible;
   - implementacion: `NOT_STARTED`.

4. **M4 - Staging / beta readiness**
   - estado: `PLANNED`;
   - depende del cierre competente de M2 y M3 o excepciones explicitas.

5. **M5 - Post-MVP domain growth**
   - estado: `DEFERRED_POST_MVP`.

## Seleccion de siguiente responsabilidad

Este cierre no selecciona M3, no inicializa un Product TaskCycle M3 y no crea
R010.

La siguiente responsabilidad debe volver a `ADV-FITFLOW-DEVELOPMENT` para
seleccion explicita a partir del baseline post-M2.

## Reconciliacion posterior a cada milestone

Al cerrar cada milestone:

- confirmar logro del objetivo macro;
- reexaminar deuda deferred ahora elegible;
- incorporar trabajo nuevo descubierto;
- retirar o marcar elementos superseded;
- reconsiderar orden, particion o combinacion de milestones;
- preservar evidencia de proceso sin convertirla silenciosamente en autoridad
  de producto.

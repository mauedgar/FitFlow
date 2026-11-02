---
document_id: FF-PROGRAM-POST-REBASELINE-001
status: canonical_post_m3
machine_context: true
version: 1.4
updated: 2026-11-01
baseline_commit: cc86f1bf0744394be4ac6357ea6117280a33c5f7
baseline_tree: 62535be814a19ae22b764bd32a3826ead7373709
reconciled: 2026-09-28
---

# Programa actual de FitFlow

## Proposito

Este documento mantiene el programa accionable de FitFlow despues del cierre
competente de M3. `docs/roadmap.md` conserva las prioridades macro; este programa
organiza milestones ejecutables sin reabrir responsabilidades ya cerradas.

El repositorio es la fuente primaria. Los TASK historicos, runs, conversaciones
y artefactos locales son evidencia subordinada al baseline vigente.

## Baseline M3 confirmado (corte historico 2026-09-28)

- `develop` tiene como baseline terminal de Product M3
  `cc86f1bf0744394be4ac6357ea6117280a33c5f7`.
- tree terminal de Product M3: `62535be814a19ae22b764bd32a3826ead7373709`.
- M1 permanece `CLOSED`.
- M2 permanece `CLOSED`.
- M3 queda `CLOSED` por satisfaccion de su criterio de cierre.
- R001 permanece `CLOSED_PASS`; su clasificacion fue `A_TEST_CONTRACT_ONLY`.
- R002 permanece `CLOSED_PASS_NO_PRODUCT_DELTA`; no requirio candidato ni Phase 2.
- no existe evidencia actual que requiera iniciar R003.
- En ese corte M4 permanecia `PLANNED / NOT_SELECTED`; su seleccion posterior
  para preparacion tecnica se registra abajo sin modificar este recibo historico.
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

## Cierre de M3

Milestone:

`M3 - Persistence and configuration stability`

Estado:

`CLOSED`

Baseline terminal de Product:

`cc86f1bf0744394be4ac6357ea6117280a33c5f7`

El criterio de cierre M3 se considera satisfecho para el scope canonico
demostrado. La evidencia acumulada establece:

- reconstruccion limpia de base desde vacio hasta Alembic head: `PASS`;
- Alembic head unico: `e4f5a6b7c8d9`;
- topologia de migraciones: `SINGLE_LINEAR_CHAIN`;
- drift Alembic inesperado: `NOT_DEMONSTRATED`;
- aislamiento de base de test: `DEMONSTRATED`;
- `FF-FOLLOW-08`: `SATISFIED_BY_R002_NO_PRODUCT_DELTA`;
- `FF-FOLLOW-09`: `SATISFIED_BY_EXISTING_FORWARD_HISTORY`, con forward replay `PASS`;
- `FF-FOLLOW-10`: `SATISFIED_BY_R001`, clasificado `A_TEST_CONTRACT_ONLY`;
- no se demostro una dependencia implicita no documentada que bloquee el criterio.

R001 y R002 permanecen terminales y no se reabren. La evidencia actual no
requiere R003. El cierre de M3 no selecciona M4.

La friccion observada por shadowing del CLI de Alembic en una superficie de
ejecucion especifica permanece clasificada como `HARNESS_RUNTIME_FRICTION`; no
constituye un Product gap ni invalida la evidencia competente de reconstruccion
y drift ya demostrada.

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
   - estado: `CLOSED`;
   - baseline terminal de Product: `cc86f1bf0744394be4ac6357ea6117280a33c5f7`;
   - R001 y R002 terminales;
   - R003 no requerido por la evidencia actual.

4. **M4 - Staging / beta readiness**
   - estado documental: `PLANNED`, con prioridad de preparacion tecnica seleccionada
     por Developer/Control el 2026-11-01; no se afirma `READY_FOR_BETA_DECISION`;
   - las validaciones/ejecuciones posteriores siguen sujetas a grants acotados.

5. **M5 - Post-MVP domain growth**
   - estado: `DEFERRED_POST_MVP`.

## Seleccion historica al cierre de M3

En el corte del 2026-09-28, este cierre no inicializaba R003 ni seleccionaba M4.

`M3 CLOSED. Next milestone selection pending Developer/control decision.`

La siguiente responsabilidad debe volver a `ADV-FITFLOW-DEVELOPMENT` para una
seleccion explicita desde el baseline terminal M3.

## Reconciliacion de objetivo M4 (2026-11-01)

El Developer selecciono **M4 como prioridad de preparacion tecnica** despues de
la integracion documental del PR #35. El baseline de Control al seleccionar la
prioridad es `develop@24dc1f40afcee9bf5be5881af449fb123fe3b033`, tree
`403843fd533a876f02af622d234971d6d741b116`; SOT v5.3 permanece intacta.
Este registro actualiza la prioridad de programa, no reabre M1-M3, ni concluye
R002-R007, ni autoriza despliegue, acceso a secretos o `LAUNCH_BETA`.

El seguimiento operativo esta en [Issue #40](https://github.com/mauedgar/FitFlow/issues/40),
con deudas acotadas: [CI actual #36](https://github.com/mauedgar/FitFlow/issues/36),
[staging R002-R006 #37](https://github.com/mauedgar/FitFlow/issues/37),
[ADMIN E2E #25](https://github.com/mauedgar/FitFlow/issues/25) y
[DocImpact #39](https://github.com/mauedgar/FitFlow/issues/39).
El [slice de Profesores #38](https://github.com/mauedgar/FitFlow/issues/38)
es una continuidad MVP independiente, no un prerequisito anadido al contrato
R007. M5 continua diferido, incluyendo Billing/Payments y Membership 1:N.

La evaluacion R007 conserva exclusivamente
`READY_FOR_BETA_DECISION | NOT_READY_FOR_BETA_DECISION`; no sustituye una
decision Developer de lanzamiento. Los contratos y runbooks existentes no
acreditan por su sola presencia una prueba fresca en este nuevo HEAD.

## Reconciliacion posterior a cada milestone

Al cerrar cada milestone:

- confirmar logro del objetivo macro;
- reexaminar deuda deferred ahora elegible;
- incorporar trabajo nuevo descubierto;
- retirar o marcar elementos superseded;
- reconsiderar orden, particion o combinacion de milestones;
- preservar evidencia de proceso sin convertirla silenciosamente en autoridad
  de producto.

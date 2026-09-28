---
document_id: FF-MILESTONE-M3-001
status: closed
machine_context: true
program: FF-PROGRAM-POST-REBASELINE-001
post_m2_baseline: 60903101384713f8b1c51d18644ac134fab8f87c
terminal_product_baseline: cc86f1bf0744394be4ac6357ea6117280a33c5f7
terminal_product_tree: 62535be814a19ae22b764bd32a3826ead7373709
closed: 2026-09-28
---

# M3 - Persistence and configuration stability

## Macro goal

Demostrar que persistencia y configuracion pueden reproducirse desde cero sin
drift no explicado y sin reescribir historia aplicada.

## Estado de cierre

```yaml
M3:
  state: CLOSED
  closure_criterion: SATISFIED
  terminal_Product_baseline: cc86f1bf0744394be4ac6357ea6117280a33c5f7
  terminal_Product_tree: 62535be814a19ae22b764bd32a3826ead7373709

R001:
  TaskCycle: TASKCYCLE-FITFLOW-M3-R001-REDIS-CONFIGURATION-PROFILE-CONTRACT-001
  classification: A_TEST_CONTRACT_ONLY
  terminal_disposition: CLOSED_PASS

R002:
  TaskCycle: TASKCYCLE-FITFLOW-M3-R002-PERSISTENCE-INVARIANT-CONTRACT-001
  classification: C_ALREADY_SATISFIED_NO_PRODUCT_DELTA
  terminal_disposition: CLOSED_PASS_NO_PRODUCT_DELTA

R003:
  initialized: false
  required_by_current_evidence: false

M4:
  selected: false
```

## Trabajo agrupado

- rebuild de base de test desde cero hasta Alembic head;
- `alembic check` sin drift inesperado;
- FF-FOLLOW-08: defaults/checks/timestamps que deban existir en DB;
- FF-FOLLOW-09: estrategia forward-only para migraciones historicas;
- FF-FOLLOW-10 residual: contrato claro de Redis por perfil;
- mantener `fitflow_test` aislada de la DB de desarrollo.

## Reconciliacion de responsabilidades

| Concern | Disposicion de cierre | Evidencia |
| --- | --- | --- |
| clean database reconstruction | `SATISFIED` | empty-to-head `PASS` |
| single valid Alembic head | `SATISFIED` | `e4f5a6b7c8d9` |
| unexpected schema drift | `SATISFIED` | no unexpected Alembic drift demonstrated |
| test database isolation | `SATISFIED` | isolation demonstrated |
| `FF-FOLLOW-08` | `SATISFIED_BY_R002_NO_PRODUCT_DELTA` | no Product gap; no migration required |
| `FF-FOLLOW-09` | `SATISFIED_BY_EXISTING_FORWARD_HISTORY` | forward replay `PASS`; no migration rewrite required |
| `FF-FOLLOW-10` | `SATISFIED_BY_R001` | `A_TEST_CONTRACT_ONLY` |
| undocumented implicit dependencies | `NO_BLOCKING_DEPENDENCY_DEMONSTRATED` | accumulated M3 gates satisfy the canonical criterion |

No permanece un Product gap M3 demostrado. R003 no se requiere por la evidencia
actual y no fue inicializado.

## Runtime de desarrollo

El contrato de tooling de test se resuelve fuera de M3 mediante dependencias
declaradas en `pyproject.toml`/`uv.lock`. M3 no debe volver a depender de
un entorno Python legacy como fuente de verdad; `backend/.venv` es el entorno local canonico.

La obstruccion observada en una invocacion de `alembic check` por module
shadowing pertenece a esa superficie de ejecucion y se conserva como
`HARNESS_RUNTIME_FRICTION`. No demuestra un Product gap ni invalida la evidencia
competente previa de reconstruccion, head lineal y ausencia de drift inesperado.

## Restricciones

- no reescribir migraciones aplicadas;
- no promover Membership 1:N;
- no mezclar schema hardening con features de negocio.

## Criterio de cierre

El criterio M3 se considera satisfecho para el scope canonico demostrado: un
entorno limpio puede levantar DB/configuracion, migrar a head y ejecutar sus
gates sin dependencias implicitas no documentadas que hayan sido demostradas
como bloqueantes.

Este cierre no eleva el estandar a perfeccion generica, hardening hipotetico ni
resiliencia futura no demostrada. Tampoco selecciona M4.

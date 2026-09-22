---
document_id: FF-MILESTONE-M3-001
status: planned
machine_context: true
program: FF-PROGRAM-POST-REBASELINE-001
post_m1_baseline: f152b8336245b01da1cea75da81b5a3c4e1a8420
---

# M3 - Persistence and configuration stability

## Macro goal

Demostrar que persistencia y configuracion pueden reproducirse desde cero sin
drift no explicado y sin reescribir historia aplicada.

## Trabajo agrupado

- rebuild de base de test desde cero hasta Alembic head;
- `alembic check` sin drift inesperado;
- FF-FOLLOW-08: defaults/checks/timestamps que deban existir en DB;
- FF-FOLLOW-09: estrategia forward-only para migraciones historicas;
- FF-FOLLOW-10 residual: contrato claro de Redis por perfil;
- mantener `fitflow_test` aislada de la DB de desarrollo.

## Runtime de desarrollo

El contrato de tooling de test se resuelve fuera de M3 mediante dependencias
declaradas en `pyproject.toml`/`uv.lock`. M3 no debe volver a depender de
un entorno Python legacy como fuente de verdad; `backend/.venv` es el entorno local canonico.

## Restricciones

- no reescribir migraciones aplicadas;
- no promover Membership 1:N;
- no mezclar schema hardening con features de negocio.

## Criterio de cierre

Un entorno limpio puede levantar DB/configuracion, migrar a head y ejecutar sus
gates sin dependencias implicitas no documentadas.

---
document_id: FF-ISSUE36-PR42-NO-DUPLICATE-WORKFLOWS-20261103-001
status: review_required
issue: 36
baseline_develop: 63bc0b9e026c1c395c33f585caf2bf0a9b160c06
baseline_develop_tree: c7257949abbc6e41ca8d09de7518d104e5bd3b30
predecessor_pr42_commit: 56815f2a780ab1ab5c5c1b40e1c45fde67759a29
predecessor_tree: c1af9ac2bcb4b5b8e06075878cc74393a59a6254
canonical_sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# Issue #36 — PR #42: evitar la duplicación de CI

## Reconciliación de ownership y alcance

En `develop`, [PR #70](https://github.com/mauedgar/FitFlow/pull/70)
ya integró `.github/workflows/fitflow-baseline-ci.yml` y el
clasificador Git, con CI real en PR Ready y en `push develop`,
más negativa `Draft=NOT_RUN`. La ejecución post-merge
[41742296185](https://github.com/mauedgar/FitFlow/actions/runs/41742296185)
concluyó SUCCESS: siete tests de clasificador, backend PG15/Redis7
243 PASS y frontend 24 PASS, lint/build. No se transfieren esos
resultados al candidato PR42.

La anterior PR42, aún DRAFT y no integrada, proponía en paralelo:
- `frontend-regression.yml` nuevo con los mismos tests, lint
  y build ya cubiertos por el baseline;
- añadir `pull_request` y `push develop` al
  `deterministic-ci.yml`, repitiendo backend PostgreSQL/Redis
  y validación portable por cada cambio.

**Esta reparación elimina esas dos activaciones duplicadas**:
se borra del árbol candidato `frontend-regression.yml`
(no existe en develop) y se conserva **exclusivamente**
`workflow_dispatch` en `deterministic-ci.yml`. El
validador manual permite `subject_sha`, `expected_tree`,
`operation_id`, `execution_attempt_id`, y conserva el
generador de request/receipt, checkout del contrato portable
v0 inmutable y publicación del artefacto. No se autoriza
repetir un intento anterior ni usar un receipt para decidir
semántica Product.

Se preservan las mejoras de reproducibilidad de PR42:
acciones por commit, `ubuntu-24.04`, Python 3.11.17,
Node 22.23.4, contenedores PG15/Redis7 por digest;
sin agregar dependencias ni secretos.

## Riesgos y deudas no ocultadas

La IR004 previa de PR42 (0 findings/3 advisories A01/A06/A07,
NO_RECOMMEND) pertenece a su árbol anterior. Este nuevo candidato
requiere nueva Independent Review original; **no declara PASS
histórico**. Las mejoras acotadas de A06 son verificables
en los pins existentes, mientras A01 real auth browser E2E y
A07 Passlib crypt deprecated **no se resuelven ni dejan de
ser deuda Product** por retirar duplicaciones. Deben seguir
en sus owners y DoD; no se inventará 0A por reetiquetarlas.

PR68 mantiene sus workflows especializados bcrypt/Chrome/
Nginx/schema y sus advisories operativos A10/A12/A13;
PR42 no altera sus archivos ni cancela sus validaciones.
La consolidación de esos flujos se decidirá sólo cuando
sus candidatos sean competentes/integrados, sin modificar
PR68 congelado.

## Validación / integración

Comparar contra develop actual: único cambio de código
en `.github/workflows/deterministic-ci.yml` y el
presente DocImpact. Confirmar que `frontend-regression.yml`
ya no es parte del diff/árbol final y que el manual
`workflow_dispatch` conserva entrada, pinning, pruebas,
generación y validación de receipt.

Validaciones negativas: ninguno de `pull_request`,
`push`, `pull_request_target` como evento; no
reintroducción del frontend automático; sintaxis YAML;
identidad de exacto commit/tree y ausencia de secretos.

El workflow manual no se ejecuta automáticamente para
este candidato; ese estado es `NOT_RUN`, no PASS.
Una validación manual por SHA exacto sólo si existe el
grant competente y no duplica una ejecución anterior.
Se requiere una nueva IR independiente y autorización
Product distinta para la aceptación e integración.
Issue #36 permanece OPEN por deuda diferenciada.

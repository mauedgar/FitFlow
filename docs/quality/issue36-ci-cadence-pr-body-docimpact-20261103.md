---
document_id: FF-ISSUE36-CI-CADENCE-DOCIMPACT-20261103-001
status: review_required
issue: 36
baseline_develop: c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d
baseline_tree: 9a2033e862535d6c0dc72b97a284811b1f401175
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# Issue #36 — Retirar el bot destructivo de descripciones

## Hallazgo y decisión limitada

La [IR001 independiente](https://github.com/mauedgar/FitFlow/pull/69#issuecomment-6607461351)
del candidato anterior confirmó **F01 MEDIUM y dos advisories A01/A02**.
Aunque el bot leyera dos veces el cuerpo de un PR, una edición humana
entre el último GET y el PATCH podía sobrescribirse. Los mensajes
de commits no sanitizados también entraban al Markdown del resumen.
El workflow anterior se ejecutaba con `opened`, `reopened` y
`synchronize` y recreaba el cuerpo entero del PR en cada actualización.

La reparación elimina por completo
`.github/workflows/auto-pr-description.yml`: ningún job ni token queda
autorizado a reescribir automáticamente cuerpos de PR por este
mecanismo, y no hay carrera de lectura-escritura ni Markdown generado
a partir de mensajes de commit. No hay coste de runner para ese bot.

Se agrega `.github/pull_request_template.md`, **plantilla pasiva**:
la persona autora escribe y modifica libremente la descripción, con
sugerencias breves de propósito, issue, SHA/tree, tests/NOT_RUN,
DocImpact, IR y aceptación. No envía API requests, no ejecuta
scripts, no requiere permisos de escritura, secrets, LLM ni
dependencias, y no crea gates/roles/autoridad Product.

## Activación / A01

La plantilla solo aparece para **nuevos PR** cuando el archivo está
en la rama **default** del repositorio, observada actualmente como
`develop`. No modifica cuerpos de PR abiertos ni se activa por
crear este candidato: hay que aceptar/integrar primero. Los
workflows cargados desde la rama base pueden seguir activos antes
de la integración; no declarar protección retroactiva. El gate
post-merge apropiado es verificar la eliminación del workflow en
`develop` y la plantilla en la rama default; observar un PR
posterior, sin crear uno artificialmente solo para la prueba.

## Cobertura / validación y límites

Negativos a comprobar contra Git tree inmutable: archivo
`auto-pr-description.yml` ausente, `.github/pull_request_template.md`
presente y sin scripts, workflows, GitHub API, secretos o
referencias a mensajes de commits. Así se elimina F01 por
construcción y A02 por ausencia de entrada no confiable;
la condición de activación de A01 queda descrita con precisión,
no suponemos efectos previos a la integración.

El resto de [Issue #36](https://github.com/mauedgar/FitFlow/issues/36#issuecomment-6607251180)
permanece **ABIERTO**: seis validaciones de PR acumulativos,
backend/frontend duplicados, filtros por diff contra `develop`,
pruebas completas en un candidato congelado y checks después
de integrar. Esa refactorización corresponde a otro write-set
competente; **no** modifica este PR ni #68. El procedimiento
acordado conserva verificaciones dirigidas durante reparación,
CI amplia exacta una vez por candidato y una IR independiente.

No cambia Product/API/DB, migrations, deps, credenciales,
protecciones de rama ni configuración de stages. Requiere una
nueva IR original en contexto independiente sobre SHA/tree
actual y aceptación Developer antes del merge.

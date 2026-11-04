---
document_id: FF-ISSUE44-PR45-DEPENDABOT-PASSIVE-20261103-001
status: review_required
issue: 44
base_develop_commit: 63bc0b9e026c1c395c33f585caf2bf0a9b160c06
base_develop_tree: c7257949abbc6e41ca8d09de7518d104e5bd3b30
predecessor_pr45: 52ced6b3da17b00a5f086d73d0424b4e062e0960
predecessor_tree: d47415b852418c826d5127cc6964ff7a04ffd4e7
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# PR45 — Dependabot sin reintroducir un workflow obsoleto

## Alcance y reconciliación

PR69 fue integrado en develop@daee5694... y **eliminó**
`.github/workflows/auto-pr-description.yml`, sustituyéndolo por
`.github/pull_request_template.md`. PR70 integró una CI básica
scope-aware; develop actual es
`63bc0b9e026c1c395c33f585caf2bf0a9b160c06`.
El candidato anterior PR45 todavía modificaba el bot obsoleto
para omitir PRs de Dependabot. Como el bot ya no existe
en develop, preservar ese archivo lo **resucitaría** y
volvería a escribir descripciones humanas. La reparación
elimina ese archivo del árbol PR45, sin alterar el blob
`.github/dependabot.yml` ya revisado. La diferencia efectiva
frente a develop queda en la nueva configuración Dependabot
y este DocImpact, sin ningún nuevo workflow ejecutable.

## Contrato propuesto

`.github/dependabot.yml` declara ecosistemas uv raíz,
npm frontend y github-actions raíz, cron diario
09:00 America/Argentina/Cordoba, cooldown de un día,
máximo cinco PRs de version updates por ecosistema.
No utiliza secretos, registries privados, ejecutables
de terceros ni merge automático. Actualizaciones se
proponen mediante PR y requieren la aceptación habitual.

## Límites que no son errores probados de código

La IR003 anterior ([original](https://github.com/mauedgar/FitFlow/pull/45#issuecomment-6567797558))
fue 0 findings / 1 advisory A01 operativo, NO_RECOMMEND
sobre un SHA/tree distintos. El updater uv de Dependabot
solo funciona al existir la configuración en la rama
predeterminada `develop`; este PR Draft no puede
demostrar ejecución del bot real. GitHub lee el archivo
cuando se integra, por lo que el primer update uv
real, su respectivo lock regenerado, `uv lock --check`
y la CI exacta siguen `NOT_RUN`; tampoco hay prueba
de fallo en este proyecto. El defecto reportado en
dependabot-core #15842 es un riesgo externo, no un
fallo reproducido aquí.

La normalización `pyproject.toml + uv.lock` de la
Issue44 permanece en la línea PR46 y su descendiente
integrado en el candidato de seguridad PR68, **sin
modificar manualmente locks o hashes** en este PR.
PR68 conserva su propia revisión y sus advisories.

## Criterios de validación

Examinar fuente Git inmutable y árbol completo;
la ruta del bot viejo DEBE estar ausente; la plantilla
nativa DEBE permanecer. El manifest Dependabot debe
ser idéntico al blob revisado, sin cambios de paquetes,
dependencias, permisos o secretos. Para un PR Draft,
el baseline CI `scope` puede pasar y suites frontend
/backend quedar `SKIPPED` correctamente.

Solicitar una nueva IR independiente sobre nuevo
SHA/tree. La aceptación exige 0 findings Y 0 advisories
y un ruling competente sobre cómo tratar la activación
operativa, sin alegar ejecución de Dependabot antes de
integración. La issue 44 no se cierra con este slice.

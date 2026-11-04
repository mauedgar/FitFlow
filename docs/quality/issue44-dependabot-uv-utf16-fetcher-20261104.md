---
document_id: FF-ISSUE44-DEPENDABOT-UV-UTF16-FETCHER-20261104-001
status: review_required
issue: 44
baseline_develop_commit: b4f4993d7454aa6b49e80e73026a20770f7a8b11
baseline_develop_tree: 75a9c79214ecf72b14052606a4a66ae5868e7c70
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# Issue #44 — Dependabot uv: fallo nativo de codificación

## Datos reales y causa

El piloto anterior integró PR #45 con excepción operativa explícita
A01 para obtener evidencia alojada. Los updates de Dependabot uv
[41751332238](https://github.com/mauedgar/FitFlow/actions/runs/41751332238)
y [41751336417](https://github.com/mauedgar/FitFlow/actions/runs/41751336417)
terminaron FAILURE en el mismo commit
`b4f4993d7454aa6b49e80e73026a20770f7a8b11`.
Ambos fallaron en `Dependabot::Python::SharedFileFetcher` al
buscar requisitos: `invalid byte sequence in UTF-8` en
`String#scan`, **antes de ejecutar uv lock**. Se conserva
cada intento terminal; no hay autorización de retry.

El árbol Git contiene archivos *.txt heredados en UTF-16
con BOM, por ejemplo:
- `backend/requirements_backend.txt`,
  blob `5bb74944e868eaee79e11ec646ae337f4bae2de1`;
- `frontend/requirements_frontend.txt`,
  blob `d9519d6f39a8dcabf1c762a8664cd8dce56ab00d`.

El GitHub blob decoder UTF-8 falla en ambos byte 0xFF/posición 0;
la API Contents sí puede transcodificarlos para lectura. El
fetcher de Dependabot uv enumera archivos `.txt` y `.in`
y procesa recursivamente requisitos. El log nativo no identifica
cuál de los dos produjo el primer fallo; ambos son incompatibles
con la lectura UTF-8 prevista.

Este fallo es **distinto** de dependabot-core #15842 (comando
`uv lock <version>`), cuya sintaxis ya fue corregida en
código público v0.403.0. No usar una prueba local del CLI
como prueba alojada.

## Reparación estrictamente acotada

Sólo el bloque `package-ecosystem: uv` del YAML de Dependabot
recibe `exclude-paths`:
`backend/**` y `frontend/**`.

Así sigue buscando `pyproject.toml` y `uv.lock` en la raíz,
manteniendo la fuente Python que Issue44 normalizará. Evita
escanear requisitos heredados UTF-16 y las referencias internas
`-r` entre archivos de backend. El ecosistema `npm` sigue
escaneando `/frontend`; GitHub Actions no cambia.

**Riesgo reconocido:** Los requisitos Python exclusivos de
subdirectorios excluidos dejarán de recibir propuestas uv
individuales; no se los declara ausentes ni se los elimina
del repositorio. Issue44 conserva su DoD de alinear los
exports runtime/test con `pyproject.toml`+`uv.lock` para
no perder cobertura de dependencias. Este cambio NO modifica
las versiones, hashes, autenticación, seguridad ni datos, y
no resuelve la separación de PR46 y PR68.

La opción `exclude-paths` está documentada por GitHub para
filtrar manifiestos durante el escaneo; su mera configuración
no equivale a runtime PASS. Tampoco un job FAIL anterior
se convierte retroactivamente en success.

## Evidencia y aceptación

Exigir examen del blob YAML exacto, cambios mínimos,
parseo/eventos y casos de exclusión positivos/negativos
(root autorizado, backend y frontend excluidos para uv,
frontend npm todavía activo), CI nativa exacta y revisión
independiente en contexto separado. El test definitivo
es otro update alojado *nuevo* sobre el futuro merge
aceptado (no repetir jobs fallidos). Inspeccionar logs,
diff de `pyproject.toml` y `uv.lock`, `uv lock --check`
y resultados de CI antes de aceptar cualquier PR del bot.

A01 queda OPEN mientras no se compruebe ese update alojado.
No se configura auto-merge, se cambian credenciales,
instalan dependencias ni se accede a DB reales.

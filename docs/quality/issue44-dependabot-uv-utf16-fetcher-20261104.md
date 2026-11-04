---
document_id: FF-ISSUE44-DEPENDABOT-UV-UTF16-FETCHER-20261104-001
status: review_required
issue: 44
baseline_develop_commit: b4f4993d7454aa6b49e80e73026a20770f7a8b11
baseline_develop_tree: 75a9c79214ecf72b14052606a4a66ae5868e7c70
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
predecessor_pr81_commit: c3d27394836128e4a924950c9e8f746c4f4724c6
acceptance: false
---

# Issue #44 — Dependabot uv: reparar codificación UTF-16 sin perder cobertura

## Evidencia nativa original

El piloto PR45 activó Dependabot en `develop@b4f4993d...`.
Los dos jobs alojados uv
[41751332238](https://github.com/mauedgar/FitFlow/actions/runs/41751332238)
y [41751336417](https://github.com/mauedgar/FitFlow/actions/runs/41751336417)
terminaron FAILURE antes de `uv lock`:
`invalid byte sequence in UTF-8`, desde
`Dependabot::Python::SharedFileFetcher#fetch_child_requirement_files`.
**No se relanzan** los intentos terminales.

Las dos rutas originales tienen BOM UTF-16 LE; la recuperación
binaria por GitHub blob da UnicodeDecodeError byte 0xff posición 0,
mientras la vista Contents devuelve su texto decodificado:
- `backend/requirements_backend.txt`, blob previo
  `5bb74944e868eaee79e11ec646ae337f4bae2de1`,
  1980 bytes, BOM+989 caracteres ASCII,
  56 líneas de dependencias, 56 CRLF;
- `frontend/requirements_frontend.txt`, blob previo
  `d9519d6f39a8dcabf1c762a8664cd8dce56ab00d`,
  1282 bytes, BOM+640 caracteres ASCII,
  34 líneas de dependencias, 34 CRLF.

La rama inicial de PR81 intentó `uv.exclude-paths` para
`backend/**` y `frontend/**`. La [IR001 independiente
sobre el SHA anterior](https://github.com/mauedgar/FitFlow/pull/81#issuecomment-6619838626)
reportó 0 findings y DOS advisories MEDIUM:
A01 posible pérdida de cobertura de actualizaciones Python
y A02 eficacia alojada no comprobada. Por tanto se **descarta
la exclusión por directorios** y se conserva el escaneo completo.
No se reclama PASS retroactivo de la IR001.

## Reparación actual — única transformación de contenido

Ambos archivos de requisitos se convierten **de UTF-16 LE con
BOM a UTF-8 sin BOM**, manteniendo exactamente el contenido
decodificado excepto el BOM inicial. Se conservan los caracteres,
los saltos de línea CRLF, el orden, todas las líneas, nombres
de paquetes, versiones, marcadores, referencias `-r`,
comentarios y terminadores. No se regeneran paquetes ni hashes,
no se editan `pyproject.toml` o `uv.lock`, ni se cambian
requisitos de seguridad/usuarios reales.

La configuración `.github/dependabot.yml` vuelve al blob
original de `develop` `82ecd5b59044b4a2e0c1217023f36a34e654d097`,
SIN `exclude-paths`: uv continúa evaluando raíz y
subdirectorios, npm conserva `frontend` y GitHub Actions
conserva su ruta. De este modo se elimina el riesgo introducido
por la primera reparación: **no se sacrifican rutas de
actualización Python** para evitar el decoder.

## Precondiciones, pruebas y riesgos

El owner de este cambio acotado es Issue44, no los PR46/PR68
congelados; esos PR contienen ramas divergentes con versiones,
lockfiles y hashes distintos. Deben reconciliar el formato
UTF-8 de sus exports al preparar cualquier futuro candidato
integrado, sin revivir Passlib ni mezclar dependencias.

Validación negativa prevista en **el nuevo SHA/tree**:
- blobs UTF-8 recuperables y sin BOM;
- texto original decodificado byte-a-byte equivalente
  tras quitar sólo `U+FEFF`; conservar 56/34
  líneas no vacías y 56/34 CRLF;
- Dependabot YAML igual al `develop` previo,
  sin exclusiones ni auto-merge;
- `git diff` y `CI` exactos; no cambios
  fuera de estos dos archivos y DocImpact;
- independiente WEB_INLINE IR002 original sobre SHA/tree
  nuevo, no transferir el resultado IR001.

**Límite operativo:** sólo la siguiente ejecución original
y alojada de Dependabot uv sobre un commit aceptado en
la rama default puede probar que ya supera el fetcher.
A02 permanece NOT_RUN hasta ese efecto; puede aparecer
otro defecto no relacionado. Ningún job previo se reintenta,
ningún PR del bot se acepta automáticamente y la
normalización de fuentes/lock Issue44 sigue ABIERTA.

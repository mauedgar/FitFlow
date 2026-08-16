---
document_id: FF-AI-ARTIFACTS-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Artefactos de contexto

## Inventarios de directorios

Nombres activos exactos:

- `estructura_Directoriosbackend.txt`;
- `estructura_Directoriosfrontend.txt`;
- `estructura_Directoriostotal.txt`.

El archivo contiene header de metadata y árbol de directorios/archivos
permitidos. Excluye artefactos irrelevantes y secretos; no resume contenido.

```text
# format: fitflow-directory-inventory/v1
# scope: backend
# generated_at: 2026-08-16T00:00:00-03:00
# baseline_revision: NO_COMMIT
# working_tree_fingerprint: sha256:...
# generator_version: ...
# exclusions_profile: default-v1
backend/
  app/
    services/
      booking_service.py
```

## Estructura de clases

Nombre: `estructura_de_clases_<YYYY-MM-DD>.xml`. Es un grafo total por defecto;
el atributo `scope` indica cobertura. Si se ejecuta más de una vez el mismo día,
el archivo activo se reemplaza atómicamente y el run queda en `INDEX_RUN.md`.

Debe validar contra `.ai/contracts/structure-graph.xsd`. Incluye símbolos,
ubicaciones, imports y relaciones; una relación inferida declara
`confidence="low|medium|high"` y `source`.

El seed puede omitir rangos y declarar `evidenceStatus="INFERRED"` cuando la
clase procede del vocabulario canónico pero el código no fue parseado. Ese nodo
sirve para orientación, no como cita de código. Repomix/repo-packager debe reemplazarlo
por rangos y hash verificados.

## Bundle Repomix

Un bundle por ejecución/scope. Debe aplicar las mismas exclusiones, registrar
config hash y permanecer en staging/exports, no en docs canónicos.

## Context Package

Formato neutral validado por `context-package.schema.json`. Contiene pregunta,
scope, baseline, presupuesto, evidencia y relaciones. No incluye archivos
completos salvo justificación explícita.

## Freshness

| Estado | Condición | Uso |
| --- | --- | --- |
| FRESH | baseline/fingerprint coincide | permitido |
| PARTIAL | coincide, pero hay archivos `UNPARSED` | permitido con warning |
| STALE | revisión/fingerprint difiere | prohibido para edición |
| INVALID | schema/hash falla | prohibido |

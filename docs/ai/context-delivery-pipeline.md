---
document_id: FF-AI-PIPELINE-CONTEXT-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Pipeline de entrega de contexto

## Secuencia

```text
role need
  -> Explorer
  -> ContextRequest
  -> ContextPackagerPort
  -> repo-packager
  -> ContextPackageResult
  -> Explorer sufficiency decision
  -> deliver or request expansion
```

## Entrada obligatoria

`task_id`, `run_id`, `consumer_role`, `scope`, `baseline`, `mode`, `query` o
`paths`, profile, budget y exclusions hash.

## Salida

`status`, paths requested/included/omitted, candidates, provenance, token
estimate, content hash, warnings y reason code. El status puede ser `COMPLETE`,
`PARTIAL`, `EMPTY`, `STALE`, `TOO_MANY_PATHS` o `ERROR`.

## Reglas

1. La misma entrada y snapshot produce el mismo hash semantico.
2. Timestamps no forman parte del hash semantico.
3. Ningun path fuera de allowlist se incluye.
4. Source material, secrets, envs, caches, outputs y archivos superseded se
   excluyen por frontera efectiva.
5. `repo-packager` no solicita otra ronda ni modifica Run State.
6. Explorer no entrega candidatos sin lectura real cuando el siguiente rol
   puede editar o aprobar.

## Gaps conocidos

La implementacion actual requiere corregir exclusions de `.env`, matching de
globs, carga de `.repomixignore`, normalizacion Windows y seleccion de archivos
irrelevantes bajo presupuestos pequenos antes de considerarse vNext compliant.

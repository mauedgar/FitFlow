# Tasks

Convencion:

```text
.ai/tasks/<TASK-ID>/
```

Cuando existe GitHub Issue sincronizada, la Issue es la TASK principal y el
archivo local es un espejo validable. Sin adapter disponible, un TASK local
aprobado puede gobernar un run offline; debe registrar `github_issue: null`.

Una task simple puede omitir artefactos no aplicables, pero toda ejecucion
produce `REVIEW.md`, `VALIDATION.md` y `RESULT.md`. Los JSON del run se guardan
en `.ai/runs/<run_id>/`.

`FF-AI-000` a `FF-AI-012` son backlog v4 superseded. El roadmap activo del AI
Core esta en `docs/implementation-roadmap.md` del repositorio Tecnotron-ai.
El antiguo mirror vNext se preserva como evidencia de migracion en
`.ai/backlog/archive/vnext.yaml`. No es backlog activo, no expresa estado
corriente de Tecnotron-ai y no debe consumirse como autoridad operativa. El
reemplazo v4 se registra en `.ai/tasks/v4-supersession.yaml`.

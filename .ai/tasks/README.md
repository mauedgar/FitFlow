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

`FF-AI-000` a `FF-AI-012` son backlog v4 superseded. El roadmap activo esta en
`docs/ai/roadmap-vnext.md`; el reemplazo machine-readable se registra en
`.ai/tasks/v4-supersession.yaml`.

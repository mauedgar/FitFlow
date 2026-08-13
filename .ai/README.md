# .ai - Area operativa de tareas

Esta carpeta no contiene arquitectura del producto. Contiene contratos y resultados de ejecucion.

## Estructura

```text
.ai/
├── README.md
├── templates/
├── tasks/
├── prompts/
└── local/
```

- `templates/`: formatos estables.
- `tasks/`: tareas que necesitan artefactos en repo.
- `prompts/`: prompts reutilizables de configuracion/investigacion.
- `local/`: transcripts, logs, dumps y pruebas temporales. Debe ignorarse en Git y en contexto de agentes.

## Regla

Una task pertenece a FitFlow, no a Codex ni Aider. Las lanes pueden tener notas separadas, pero el `RESULT.md` aceptado es unico.

El proceso completo vive en `docs/process/task-lifecycle-and-reporting.md`.

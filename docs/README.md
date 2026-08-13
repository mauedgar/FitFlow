# FitFlow Docs

Esta carpeta contiene la **documentacion canonica activa** de FitFlow. Esta pensada para humanos y agentes: amplia donde el conocimiento debe ser durable y selectiva respecto de lo que se carga en contexto.

## Conjunto canonico

- `SOURCE_OF_TRUTH.md`: jerarquia de autoridad y reglas de reconciliacion.
- `architecture.md`: arquitectura actual, responsabilidades y target.
- `domain.md`: entidades, relaciones e invariantes del negocio.
- `current-state.md`: snapshot vigente.
- `roadmap.md`: direccion hacia el MVP y evolucion posterior.
- `quality-and-validation.md`: testing, quality gates y evidencia.
- `process/`: ciclo de tareas, Jira, reportes y ejecucion humana/agente.
- `adr/`: decisiones arquitectonicas aceptadas.
- `ai/`: pipelines de IA, contexto, indexador y AiderDesk.
- `formal/`: documento de consulta consolidado.
- `archive/`: historico/superseded; fuera del contexto activo por defecto.

## Regla editorial

Un documento activo debe responder una pregunta concreta.

- El codigo dice **que hace hoy**.
- `current-state.md` dice **donde estamos**.
- `architecture.md` y `domain.md` dicen **como se organiza y que significa**.
- un ADR dice **por que se tomo una decision durable**.
- `roadmap.md` dice **hacia donde vamos**.
- `.ai/tasks/*/RESULT.md` dice **que ocurrio en una task concreta**.
- Jira dice **que trabajo existe y en que estado esta**.

No usar `docs/` como bitacora de cada ejecucion.

## Contexto de agentes

La existencia de muchos documentos no significa cargarlos todos. `AGENTS.md` es la entrada compacta; los documentos restantes se consultan por necesidad. El Project Index puede localizar secciones/documentos, pero nunca reemplaza la verificacion del codigo.

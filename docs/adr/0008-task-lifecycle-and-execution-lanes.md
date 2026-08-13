# ADR 0008: Ciclo de tareas y execution lanes

- **Estado:** Accepted
- **Fecha:** 2026-08-13

## Contexto

FitFlow usa desarrollo humano, Codex y AiderDesk. Sin un contrato comun, los resultados, estados y decisiones pueden dispersarse entre conversaciones, Jira y Git.

## Decision

Adoptar un ciclo de task neutral al ejecutor:

- Jira controla estado, prioridad y milestone.
- `TASK.md` define el contrato tecnico.
- `PLAN.md` se usa solo cuando la complejidad requiere memoria durable.
- `STATUS.md` registra progreso de trabajos largos.
- `RESULT.md` normaliza el reporte final.
- Git conserva implementacion/diff/revision.
- `docs/` recibe solo conocimiento durable promovido desde resultados aceptados.

Execution lanes: `human`, `codex`, `aider`, `mixed`, `undecided`.

Estados: Backlog -> Ready -> In Progress -> Validation -> Review -> Done, con Blocked.

## Consecuencias

### Positivas
- trazabilidad entre Jira, Git y agentes;
- mismo contrato para distintos ejecutores;
- permite automatizacion futura sin redisenar el proceso;
- evita que transcripts se conviertan en documentacion.

### Negativas
- requiere disciplina para mantener TASK/RESULT;
- puede ser burocratico si se aplica completo a cambios triviales.

## Regla de proporcionalidad

- trivial: prompt + Git;
- mediana: TASK + RESULT;
- compleja: TASK + plan + RESULT;
- larga: TASK + PLAN + STATUS + RESULT.

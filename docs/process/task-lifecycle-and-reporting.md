# Ciclo de tareas y reportes - FitFlow

**Estado:** Canonico  
**Version:** 1.0 - 2026-08-13

## 1. Objetivo

Mantener seguimiento activo sin mezclar el estado del producto con logs de agentes. El mismo proceso sirve para tareas humanas, Codex y Aider.

## 2. Responsabilidades de cada sistema

```text
Jira      -> que trabajo existe, prioridad, estado, milestone
TASK.md   -> contrato tecnico de una task
PLAN.md   -> estrategia durable si la complejidad lo requiere
STATUS.md -> progreso durante ejecuciones largas
RESULT.md -> reporte tecnico final
Git       -> implementacion, diff y trazabilidad
docs/     -> conocimiento durable promovido desde resultados aceptados
```

No duplicar la misma informacion en todos los lugares.

## 3. Workflow de estados

```text
Backlog
  -> Ready
  -> In Progress
  -> Validation
  -> Review
  -> Done

In Progress / Validation / Review -> Blocked cuando exista un bloqueo real
Blocked -> Ready cuando se resuelva
Validation / Review -> In Progress si hace falta corregir
```

### Backlog
Idea o necesidad todavia no lista para ejecucion.

### Ready
Objetivo, alcance, restricciones y criterio de aceptacion suficientemente claros.

### In Progress
Existe un ejecutor trabajando sobre la task.

### Validation
La implementacion termino; se ejecutan tests/checks.

### Review
Validacion suficiente; se revisa diff/resultado/impacto.

### Done
Resultado aceptado e integrado.

### Blocked
Existe una dependencia concreta. Debe registrarse que falta.

## 4. Dimensiones Jira

Mantener pocas dimensiones estables:

### Area
- `backend`
- `frontend`
- `infra`
- `docs`
- `ai-tooling`

### Execution lane
- `human`
- `codex`
- `aider`
- `mixed`
- `undecided`

Execution lane describe quien ejecuta, no quien decide arquitectura.

### Task type
- `feature`
- `fix`
- `refactor`
- `audit`
- `test`
- `docs`
- `tooling`

### Labels excepcionales
Solo cuando aporten informacion no expresada por campos normales:
- `needs-adr`
- `needs-human-decision`
- `blocked-external`

Priority, Epic/Milestone y Sprint permanecen en las capacidades normales de Jira.

## 5. Contrato TASK.md

Debe ser corto y ejecutable:
- ID;
- titulo;
- tipo;
- estado;
- prioridad;
- area;
- lane;
- objetivo;
- contexto minimo;
- scope;
- fuera de scope;
- restricciones;
- evidencia requerida;
- criterios de aceptacion;
- validaciones esperadas;
- impacto documental esperado.

No pegar conversaciones completas.

## 6. PLAN.md y Plan mode

Una task trivial no necesita plan durable.

- pequena: prompt/Git;
- mediana: TASK + RESULT;
- compleja: TASK + plan aprobado + RESULT;
- larga: TASK + PLAN + STATUS + RESULT.

En Codex, Plan mode puede usarse para investigar/proponer antes de editar. Si el plan es relevante para reanudar o auditar el trabajo, se materializa en `PLAN.md`.

## 7. Ejecuciones separadas por agente

Una task puede contener:

```text
.ai/tasks/<TASK-ID>/
├── TASK.md
├── PLAN.md            # opcional
├── codex/
│   ├── STATUS.md      # opcional
│   └── NOTES.md       # opcional
├── aider/
│   ├── STATUS.md      # opcional
│   └── NOTES.md       # opcional
└── RESULT.md
```

Los subdirectorios guardan datos operativos de cada lane. `RESULT.md` es el reporte normalizado aceptado.

No versionar transcripts/logs gigantes; usar `.ai/local/` para material temporal.

## 8. Concurrencia

Regla: **una sola lane de escritura sobre la misma seccion conceptual a la vez**.

Puede coexistir:
- Codex implementando Booking;
- Aider auditando naming read-only.

Evitar:
- Codex y Aider modificando `booking_service.py` simultaneamente.

Usar branches/worktrees cuando exista paralelismo real.

## 9. Trazabilidad Git

Una task implementadora debe registrar, cuando aplique:
- baseline commit;
- branch/worktree;
- commits resultantes;
- diff/revision final.

Convencion sugerida una vez confirmado el Jira key:

```text
task/<JIRA-KEY>-descripcion-corta
<JIRA-KEY>: descripcion del cambio
```

Los auto-commits de una herramienta son checkpoints tecnicos, no aprobacion final.

## 10. RESULT.md como reporte

Debe responder:
- que ocurrio;
- ejecutor;
- baseline/final revision;
- archivos cambiados;
- validaciones y resultado;
- hallazgos;
- riesgos;
- decisiones propuestas;
- impacto documental;
- follow-ups.

El RESULT no debe copiar razonamiento interno ni transcript completo.

## 11. Promocion a docs

Actualizar docs/ADR solo si el resultado cambia conocimiento durable.

Ejemplos:
- implementar RRULE y cerrar legacy -> current-state/domain/ADR;
- renombrar un archivo sin cambiar significado -> normalmente no;
- cambiar ownership de una regla de negocio -> architecture/domain/ADR segun impacto.

## 12. Testing como gate

Para codigo backend, `Validation` debe preferir evidencia ejecutable:
- pytest targeted;
- suite mas amplia segun riesgo;
- Ruff;
- type checking;
- Alembic/OpenAPI si aplica.

Si una herramienta no existe, usar `UNAVAILABLE` y abrir/relacionar una task de baseline. No declarar PASS por inferencia.

## 13. Alineacion futura

Este proceso esta preparado para que Jira pueda servir como control plane de una futura orquestacion, pero el humano conserva las transiciones/decisiones mientras el flujo se estabiliza.

Symphony u otra automatizacion se estudia despues; no es requisito de esta version.

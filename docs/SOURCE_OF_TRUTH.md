# Source of Truth - FitFlow

**Estado:** Activo  
**Version:** 3.0  
**Actualizado:** 2026-08-13

## 1. Objetivo

Definir como resolver contradicciones entre codigo, tests, documentacion, decisiones, tareas e indices derivados.

## 2. Capas de verdad

### Capa 0 - Realidad ejecutable

Autoridad para responder **que existe y como se comporta hoy**:
- codigo fuente versionado;
- tests vigentes;
- configuracion;
- modelos y migraciones Alembic;
- estado reproducible del repositorio.

Los tests son evidencia ejecutable solamente para el comportamiento que realmente cubren.

### Capa 1 - Documentacion canonica

Autoridad para responder **que significa, que fronteras se respetan y que decisiones se aceptaron**:
- `current-state.md`;
- `architecture.md`;
- `domain.md`;
- `adr/`;
- `roadmap.md`;
- `quality-and-validation.md`;
- `process/`.

La documentacion no debe declarar implementada una decision futura.

### Capa 2 - Registros operativos

Trazabilidad del trabajo, no autoridad arquitectonica:
- Jira: estado/prioridad/ownership del trabajo;
- `.ai/tasks/<id>/TASK.md`: contrato de una tarea;
- `PLAN.md`: estrategia durable cuando la complejidad lo justifica;
- `STATUS.md`: progreso de una ejecucion larga;
- `RESULT.md`: reporte tecnico final;
- Git branches/worktrees/commits/diffs: evidencia de implementacion.

Un RESULT puede motivar cambios de docs, pero no reemplaza por si solo a `architecture.md`, `domain.md` o un ADR.

### Capa 3 - Contexto derivado

Ayuda a encontrar informacion:
- Project Index;
- embeddings;
- grafo de relaciones;
- pdoc;
- RepoMap;
- caches;
- bundles/resumenes de contexto.

Deben ser regenerables y, cuando sea posible, asociados a una revision Git.

### Capa 4 - Historico

`docs/archive/` contiene planes/snapshots reemplazados. Sirve para trazabilidad, no como instruccion activa.

## 3. Regla de conflicto

Si codigo, tests y docs difieren:
1. confirmar revision/estado del codigo;
2. identificar que cubren realmente los tests;
3. distinguir estado actual de target/decision;
4. no corregir silenciosamente una fuente para hacerla coincidir;
5. marcar **A revisar**;
6. resolver mediante una task delimitada y, si cambia una decision durable, actualizar docs/ADR.

## 4. Estados documentales

- **Confirmado:** verificado en codigo/tests/config vigente.
- **Accepted / Pending Implementation:** decision aprobada, implementacion no garantizada.
- **Planificado:** direccion futura.
- **A revisar:** evidencia parcial/contradiccion pendiente.
- **Historico:** ya no gobierna el presente.
- **Superseded:** reemplazado por una decision/documento posterior.

## 5. Regla de promocion

Una task modifica docs canonicos solo si su resultado cambia conocimiento durable:
- comportamiento esperado del dominio;
- responsabilidades/fronteras;
- arquitectura;
- source of truth;
- calidad/validation gates;
- proceso operativo;
- roadmap.

No actualizar docs por cambios puramente mecanicos que no cambian significado.

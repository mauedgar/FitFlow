---
document_id: FF-AGENTS-001
status: canonical
machine_context: true
version: 5.1
updated: 2026-08-25
---

# Reglas para agentes

## Precedencia

1. Codigo, tests, configuracion y migraciones verificadas.
2. `docs/SOURCE_OF_TRUTH.md`.
3. Documentacion canonica y ADR aceptados.
4. GitHub Issue aprobada o su espejo local `TASK.md` autorizado.
5. Artefactos de run asociados al baseline correcto.
6. Contexto derivado asociado al baseline correcto.

Ante contradiccion: detener la inferencia, registrar evidencia y escalar al
Planner o al desarrollador. No armonizar fuentes silenciosamente.

## Inicio obligatorio

1. Clasificar la tarea: `backend`, `frontend` o `mixed`.
2. Confirmar `task_id`, objetivo, riesgo, baseline y ownership.
3. Cargar solo los documentos declarados en `required_docs`.
4. Solicitar al Explorer un `ContextRequest` acotado cuando falte evidencia.
5. Usar `repo-packager` solo como empaquetador determinista.
6. Leer el codigo citado antes de editar.

## Flujo

`PLAN -> ROUTE -> EXPLORE -> EXECUTE -> VALIDATE -> REVIEW -> DOC_SYNC -> PENDING_ACCEPTANCE`.

Solo el desarrollador puede promover a `DONE`. Si falta contexto, volver a
`EXPLORE`; si falla la implementacion o la validacion, volver a `ROUTE`; si el
plan o la doctrina son incorrectos, volver a `PLAN`.

## Ciclo de worktree

- Toda task nace de la rama `develop` y se ejecuta en un worktree acotado
  fuera del checkout principal.
- El ciclo abre rama local y remota: `git worktree add -b <branch> <ruta>
  develop` seguido de `git push -u origin <branch>`.
- Al finalizar (merge o abandono), se cierran ambas: `git worktree remove`,
  `git branch -d <branch>` y eliminacion de la remota si quedo sin merge.
- El checkout principal permanece limpio sobre `develop` y solo recibe
  fast-forward despues del merge; nunca se trabaja directo en el.

## Autonomia

- `low`: ejecucion permitida dentro del scope.
- `medium`: ejecucion permitida con revision independiente y validacion.
- `high`: `BLOCKED_HIGH_RISK`; requiere nueva decision del desarrollador.
- No instalar o actualizar dependencias sin autorizacion explicita.
- No ejecutar comandos destructivos.
- No modificar secretos ni archivos `.env`.
- No crear commits, push, merge ni transiciones finales.
- No ampliar scope para aprovechar una edicion.
- El gasto incremental de API es `USD 0`; proveedores pagos permanecen
  deshabilitados salvo decision explicita.

## Arquitectura de producto

- Backend: `Router -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL`.
- Schemas Pydantic son contratos de borde, no persistencia.
- Services nuevos no ejecutan ORM directo.
- CRUD no define politica de negocio.
- PostgreSQL conserva estado persistente; Redis solo estado temporal con
  ownership explicito.

## Arquitectura de asistencia IA

- OpenCode es una implementacion detras de `AgentRuntimePort`, no la autoridad
  del workflow.
- TypeScript gobierna estados, retries, gates y persistencia.
- El Router aplica reglas deterministas y usa LLM solo como fallback.
- El Model Resolver selecciona capacidad y recurso; no define autoridad.
- Explorer decide que contexto necesita otro rol.
- `repo-packager` empaqueta exactamente una solicitud; no explora ni decide.
- Validator es determinista. Reviewer no valida su propia implementacion.
- OpenSpec describe cambios funcionales; no reemplaza TASK ni Run State.

## Contexto autorizado

- inventarios `estructura_Directorios<scope>.txt`;
- grafo `estructura_de_clases_<YYYY-MM-DD>.xml` cuando este fresco;
- paquetes `reduced`, `drill-down` o `expanded` de `repo-packager`;
- bundles Repomix acotados;
- resultados de retrieval evaluados;
- lecturas directas de codigo y tests.

Los artefactos derivados orientan; nunca sustituyen la lectura del codigo
antes de editar. No cargar `docs/archive/source-material/`.

## Escritura concurrente

Una sola ejecucion puede poseer una `ownership_key`. Las claves incluyen rutas,
contratos API, dominio, DB/migraciones y documentacion canonica. Si existe
interseccion, serializar las tareas.

## Evidencia

Cada ejecucion debe producir `REVIEW.md`, `VALIDATION.md` y `RESULT.md` usando
`PASS`, `FAIL`, `NOT_RUN`, `UNAVAILABLE`, `BLOCKED` o `N/A`. Los artefactos
estructurados del run usan `.ai/contracts/v2/`. Un resumen sin comando, alcance
y salida verificable no es evidencia.

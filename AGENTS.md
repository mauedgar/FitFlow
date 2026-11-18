---
document_id: FF-AGENTS-001
status: canonical
machine_context: true
version: 5.3
updated: 2026-11-14
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
La Issue gobierna la task operativa; comentarios y recibos de PR son evidencia
operativa, no doctrina canonica ni reemplazo de `docs/SOURCE_OF_TRUTH.md`.

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
Conservar `UNKNOWN` cuando falte evidencia: no convertirlo en `PASS` ni
reintentar automaticamente por inferencia.

## Ciclo de worktree

- Habitualmente la task nace de `develop` y se ejecuta en un worktree acotado
  fuera del checkout principal. Antes de crearlo, reobservar rama competente,
  HEAD/tree y baseline autorizado; no asumir `develop` si la task fija otro ref.
- Crear solo rama local y worktree desde el baseline competente verificado
  (`git worktree add -b <branch> <ruta> <ref-competente>`). Publicar una rama
  remota mediante `git push` es un efecto separado que requiere concesion
  explicita y acotada del desarrollador para esa rama y baseline; nunca es
  automatico al abrir el worktree.
- Al finalizar, la limpieza de worktree y ramas requiere permiso separado,
  comprobacion del merge exacto exitoso, arbol limpio y ausencia de owners;
  no forzar la eliminacion ni inferir permiso del cierre de la task. Un
  abandono requiere decision expresa, no se trata como merge exitoso.
- El checkout principal permanece limpio sobre `develop` y solo recibe
  fast-forward despues del merge; nunca se trabaja directo en el.

## Autonomia

- `low`: ejecucion permitida dentro del scope.
- `medium`: ejecucion permitida con revision independiente y validacion.
- `high`: `BLOCKED_HIGH_RISK`; requiere nueva decision del desarrollador.
- No instalar o actualizar dependencias sin autorizacion explicita.
- No ejecutar comandos destructivos.
- No modificar secretos ni archivos `.env`.
- Por defecto, no crear commits, push, merge ni transiciones finales. Una
  excepcion requiere concesion explicita y acotada del desarrollador para la
  accion concreta, rama y baseline; para integrar, ademas candidato SHA/tree
  exacto y revision independiente aplicable. Reobservar rama competente y
  arbol antes de actuar.
  Un `IR PASS` no concede permiso automatico ni dispensa esas condiciones.
  Autorizar un commit candidato no autoriza push, merge, aceptacion o `DONE`.
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
- Un UI Admin validado con datos en memoria o mocks no prueba autenticacion
  real E2E; mantener esa cobertura como `NOT_RUN` hasta evidencia especifica.

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

## FitFlow Product-first risk-adaptive delivery (Developer 2026-11-14)

**Specific future-process overlay:** `docs/operations/fitflow-exceptional-delivery-v1.md`
records the approved five reforms in a dedicated FitFlow Product responsibility.
For future work after competent policy integration, classify LOW/MEDIUM/HIGH/
RELEASE risk and apply proportionate CI, semantic review and advisory routing
there rather than imposing uniform 0F/0A or full repeat review on every edit.
The stricter baseline remains for token/session security, retained data,
migrations, unknown effects and launch decisions.

A bounded Developer grant may delegate **routine** candidate/merge mechanics
with exact repo, owner, scope, verified SHA/tree, check and allowed effect.
The existing "default no commit/push/merge" rule applies whenever such a
specific grant is absent; no IR/CI alone implies Product acceptance. Preserve
all frozen attempts/verdicts, including Control 013 PR107/PR109 and IR005; no
retrospective acceptance. Authorize one stable-candidate independent review
per defined review subject (extra focused security review when genuinely
needed), reuse deterministic checks during edits, and parallelize only
disjoint worktrees/write sets. OpenCode2 local dispatch remains via visible
Orca-owned terminal; Codex Cloud remains optional/experimental, not canonical.
No dependency on unrelated infrastructure for a functional product gate.

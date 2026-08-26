# FF-AUD-001 - Reconciliacion y baseline tecnico

## Baseline

- branch: `feat/FF-AUD-001`;
- worktree: `C:/Users/maued/orca/workspaces/FitFlow/feat-FF-AUD-001`;
- base: `develop@20d2616`;
- risk: `medium`;
- plan rector: `.ai/tasks/FF-LOCALv-000/PLAN.md`.

## Precedencia

1. codigo, tests, configuracion y migraciones verificadas;
2. documentacion canonica;
3. TASK y criterios aceptados;
4. evidencia historica;
5. contexto derivado.

## Wave A - Seguridad e inventario

1. verificar branch, SHA, worktree, limpieza y write scope;
2. inventariar el bundle real de `FF-LOCAL-001..010`;
3. registrar artefactos ausentes como `MISSING_HISTORICAL`;
4. no escribir en los directorios historicos.

## Wave B - Reconciliacion

Para cada task:

1. leer criterios y resultado historico;
2. localizar codigo, tests, migraciones y configuracion relacionados;
3. contrastar claims contra el baseline actual;
4. asignar estado sustentado;
5. registrar gap y proxima accion sin crear una task correctiva.

La matriz usa:

| Task | Alcance | Estado documental | Estado verificado | Evidencia | Gap | Proxima accion |
| --- | --- | --- | --- | --- | --- | --- |

## Wave C - Baseline tecnico

Ejecutar, cuando esten disponibles y sin instalar dependencias:

- controles Git;
- metadata y configuracion de mappers ORM;
- topologia y head de Alembic;
- suites smoke, unit e integration existentes;
- validacion de calidad documentada;
- health/startup y pruebas HTTP documentadas;
- comprobaciones contra `fitflow_test` solo mediante configuracion existente.

Una dependencia ausente se registra `UNAVAILABLE`. Una suite inexistente o no
ejecutada se registra `NOT_RUN`. Ninguna de ambas equivale a `PASS`.

## Wave D - Gates

### Gate 2 - Baseline conocido

Requiere una matriz completa y reproducible, aunque contenga fallos o checks no
disponibles. No requiere que el producto este sano.

### Gate 3 - Autorizacion de correcciones

Cada finding candidato debe tener evidencia reproducible, capa propietaria,
alcance, dependencias, riesgo, criterios verificables y estrategia de
validacion. Los findings DB/ORM/migraciones/dominio sin evidencia de entorno
suficiente permanecen bloqueados.

## Wave E - Evidencia y review

1. Validator produce `VALIDATION.md` con comandos y resultados;
2. Reviewer independiente revisa trazabilidad, suficiencia y scope;
3. el ejecutor consolida `RESULT.md`;
4. Lifecycle deja el estado en `PENDING_ACCEPTANCE`;
5. no se crean ni ejecutan tasks correctivas durante este run.

## Veredictos

- `BASELINE_KNOWN`;
- `BASELINE_PARTIAL`;
- `DEVELOPER_DECISION_REQUIRED`;
- `WORKTREE_BLOCKED`.

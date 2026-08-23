# FitFlow — Activación y reconciliación de Sprint 6.8

Trabaja exclusivamente en el repositorio `FitFlow`.

No inspecciones ni modifiques `FitFlow-ai`, `tecnotron-ai`, `friAgent`, Orca ni repositorios vecinos.

## Objetivo

Determinar el estado real de Sprint 6.8, terminar la curación documental sólo cuando sea mecánica y verificable, reconciliar las tasks existentes contra código/tests/configuración y dejar identificada una única siguiente TASK `READY`.

Este ciclo no implementa funcionalidades del producto.

## Autoridad

Usa este orden de autoridad:

1. Código, tests, migraciones y configuración ejecutable.
2. Documentación canónica activa.
3. TASK y evidencia de ejecución.
4. GitHub Projects, si sus referencias están disponibles localmente.
5. Índice de MCP Codebase como mecanismo de recuperación, nunca como fuente de verdad.

MCP Codebase es un servicio activo de búsqueda. No esperes que produzca un archivo dentro del repositorio.

Toda afirmación recuperada mediante MCP Codebase debe verificarse después contra archivos reales.

## Fase 0 — Seguridad del worktree

Ejecutar primero:

```bash
git status -sb
git branch --show-current
git log --oneline -5

```

Leer completamente:

- [`AGENTS.md`](http://AGENTS.md);
- reglas locales aplicables;
- índice o declaración de Source of Truth, si existe;
- documentación de lifecycle de tareas, si existe.

No sobrescribir cambios locales existentes.

Si hay modificaciones ajenas que impiden distinguir el baseline, detenerse con `WORKTREE_BLOCKED`.

No hacer:

- commit;
- push;
- pull;
- merge;
- rebase;
- reset;
- creación o eliminación de ramas;
- cambios de dependencias.

## Fase 1 — Recuperación acotada con MCP Codebase

Usar primero MCP Codebase para obtener una vista general, con un máximo inicial de seis consultas semánticas:

1. documentos canónicos que definen Sprint 6.8;
2. tasks asociadas a Sprint 6.8;
3. implementación y pruebas de capacidad/overbooking;
4. estado de schemas Pydantic y contratos;
5. estado de ClassSchedule, ClassSession y RRULE;
6. deuda técnica o tasks antiguas etiquetadas.

Después usar búsqueda textual exacta (`rg`, `git ls-files`) para confirmar rutas, símbolos y estados.

No realizar búsquedas exhaustivas si una consulta amplia ya identificó los archivos candidatos.

## Fase 2 — Inventario documental

Localizar y clasificar:

- documentos canónicos activos;
- documentos históricos o archivados;
- roadmap vigente;
- definición vigente de Sprint 6.8;
- `.ai/tasks/**`;
- tasks antiguas todavía presentes;
- referencias a GitHub Issues o GitHub Projects;
- `.github/workflows/*.yml` o `.yaml`.

Tomar como conjunto esperado de referencia `FF-LOCAL-001` a `FF-LOCAL-007`, pero no inventar archivos ni estados si los identificadores reales difieren.

Para cada documento, indicar:


| Documento | Clasificación                                  | Estado                                    | Evidencia         | Acción                                  |
| --------- | ---------------------------------------------- | ----------------------------------------- | ----------------- | --------------------------------------- |
| ruta      | CANONICAL / OPERATIONAL / HISTORICAL / DERIVED | CURRENT / STALE / CONTRADICTORY / MISSING | archivo y sección | KEEP / UPDATE / ARCHIVE_PROPOSAL / NONE |


No tratar `docs/archive/**` como instrucción activa.

## Fase 3 — Reconciliación de tasks

Para cada task relacionada con Sprint 6.8:

1. leer sus criterios de aceptación;
2. localizar implementación relacionada;
3. localizar tests relacionados;
4. comprobar migraciones y configuración cuando correspondan;
5. revisar evidencia previa;
6. asignar estado sustentado.

Usar el lifecycle definido por el repositorio. Si no existe uno, reportar la ausencia y usar provisionalmente:

```text
BACKLOG
READY
IN_PROGRESS
VALIDATION
REVIEW
DONE
BLOCKED

```

Una task sólo puede considerarse `DONE` si hay evidencia reproducible suficiente. El simple hallazgo de código parecido no alcanza.

Clasificación requerida:


| Task | Alcance | Estado documental | Estado real | Evidencia | Gap | Próxima acción |
| ---- | ------- | ----------------- | ----------- | --------- | --- | -------------- |


Distinguir especialmente:

- implementada y validada;
- implementada parcialmente;
- definida pero no iniciada;
- obsoleta o absorbida por otra task;
- contradictoria con la arquitectura actual;
- bloqueada por entorno;
- sin evidencia suficiente.

## Política para tasks antiguas

No eliminar tasks completadas.

No moverlas automáticamente.

Las tasks terminadas conservan su [`TASK.md`](http://TASK.md) y su evidencia final. El conocimiento durable debe estar promovido a los documentos canónicos.

Si el repositorio ya establece un archivo histórico, proponer el movimiento del bundle completo, pero no ejecutarlo durante este ciclo.

No considerar una task histórica `DONE` como instrucción activa para una implementación nueva.

## Fase 4 — Curación permitida

Se autorizan únicamente correcciones documentales mecánicas y respaldadas por evidencia inequívoca:

- paths rotos;
- referencias a archivos movidos;
- duplicaciones exactas;
- estados claramente desactualizados respecto de evidencia ya validada;
- índices canónicos desalineados;
- referencias incorrectas entre TASK y roadmap.

Antes de modificar, registrar la evidencia que demuestra la corrección.

No realizar automáticamente cambios semánticos como:

- redefinir criterios de aceptación;
- alterar arquitectura;
- dividir o fusionar tasks;
- declarar una task obsoleta;
- cambiar decisiones de dominio;
- promover una task a `DONE` con evidencia incompleta;
- crear funcionalidades nuevas.

Si se necesita cualquiera de esos cambios, detener la curación y reportar `DEVELOPER_DECISION_REQUIRED`.

No crear todavía código productivo, migraciones ni tests funcionales.

No hacer commit.

## Fase 5 — GitHub Actions

Comprobar que los workflows se encuentren exclusivamente bajo:

```text
.github/workflows/

```

Las tasks deben permanecer en la ubicación operativa definida por FitFlow, previsiblemente:

```text
.ai/tasks/

```

No mover tasks dentro de `.github/`.

Revisar, sin modificar salvo error documental mecánico:

- si los workflows son YAML válidos;
- si sus filtros `paths` apuntan a rutas existentes;
- si los checks nombrados corresponden a comandos realmente disponibles;
- si una automatización documental vigila `.ai/tasks/**`;
- si mover una task a archive rompería algún filtro;
- si existen referencias a directorios antiguos.

No crear un workflow nuevo durante este ciclo. Si falta uno, proponerlo como task separada.

## Fase 6 — Selección de la siguiente task

Seleccionar una sola task para continuar Sprint 6.8.

Criterios:

1. pertenece realmente al alcance pendiente;
2. sus dependencias están satisfechas;
3. tiene criterios de aceptación verificables;
4. no exige resolver simultáneamente otra task;
5. puede ejecutarse mediante TDD;
6. acerca FitFlow al MVP antes que ampliar tooling o laboratorio.

No implementar la task seleccionada.

Si ninguna cumple los criterios, declarar exactamente qué falta para dejar una en `READY`.

## Verificación

Después de cualquier corrección documental ejecutar:

```bash
git diff --check
git status --short
git diff --stat
git diff

```

Si existen suites documentales ya configuradas y no requieren instalar dependencias, ejecutarlas.

No instalar nada sin autorización.

Los comandos no ejecutables deben reportarse como `UNAVAILABLE`, nunca como `PASS`.

## Entregable final

Entregar:

1. estado del worktree;
2. fuentes canónicas encontradas;
3. documentos vigentes, stale y contradictorios;
4. inventario completo de tasks de Sprint 6.8;
5. tasks antiguas y tratamiento recomendado;
6. verificación de `.github/workflows/`;
7. correcciones documentales realizadas;
8. archivos modificados;
9. decisiones que requieren al Developer;
10. única siguiente task recomendada;
11. veredicto final:

```text
SPRINT_READY
CURATION_PARTIALLY_COMPLETED
DEVELOPER_DECISION_REQUIRED
WORKTREE_BLOCKED

```

Detenerse después del informe.

No implementar código, no crear PLAN de implementación y no hacer commit, push, PR ni merge.
# Roadmap de FitFlow

**Estado:** Canonico  
**Version:** 3.0 - 2026-08-13

## 1. Principio

El objetivo es terminar un **MVP operativo** sobre un dominio estable y una base de validacion suficiente. El tooling ayuda al producto; no debe convertirse en un laboratorio que bloquee el MVP.

Se mantienen dos tracks:
- **Producto**
- **Engineering Tooling / Developer Operations**

## 2. Track de producto

### P0 - Sprint 6.8: consolidacion actual

Checkpoint:
- relaciones/cardinalidades y modelos SQLAlchemy coherentes;
- Pydantic v2 consolidado;
- ClassSchedule/RRULE con estado real resuelto;
- ClassSession/capacidad coherente;
- Booking atomico y duplicados validados;
- endpoints MVP necesarios cerrados;
- seguridad/roles revisados en alcance critico;
- **baseline pytest operativo + cobertura critica suficiente**;
- Ruff/type checking aplicables;
- docs canonicos sincronizados.
- modelos ORM normalizados al estilo SQLAlchemy 2.x sin cambios semánticos accidentales;
- integridad ORM revisada y discrepancias resueltas o explicitadas;
- enums y estados del dominio inventariados y alineados;
- contratos Pydantic v2 reconciliados con modelos y reglas del dominio;
- ClassSchedule/ClassSession consolidados con estado RRULE resuelto.

### P1 - MVP operativo rebaselined

Absorbe la intencion funcional del antiguo Sprint 7 sin sus supuestos desactualizados:
- Cliente -> Clase -> Agenda -> Sesion -> Reserva;
- Front Desk;
- capacidad/disponibilidad coherentes;
- creacion/cancelacion de Booking;
- frontend/backend por contratos actuales;
- UX minima viable;
- errores de dominio presentados correctamente.

### P2 - Stabilization

- ampliar unit/integration/API tests;
- regresiones de Booking/Session/Membership/Auth;
- concurrencia donde la integridad lo requiera;
- Alembic;
- smoke frontend;
- bugs de integracion.

### P3 - Staging / beta

Docker reproducible, environments, logging/observabilidad basica, staging y beta controlada.

### P4 - Post-MVP

Asistencia avanzada, metricas, facturacion/pagos, automatizaciones y evaluacion de extracciones solo con evidencia real.

## 3. Track Engineering Tooling / Developer Operations

### T0 - Baseline documental v3
- source of truth;
- architecture/domain/current-state/roadmap;
- ADRs;
- proceso de tasks/reportes;
- AGENTS compacto;
- archivo historico separado.

### T1 - Validation baseline
**Critico para automatizacion fiable.**
- pytest/pytest-asyncio;
- estructura de tests;
- smoke harness;
- fixtures reales;
- tests representativos de invariantes;
- comando canonico para agentes;
- resultado normalizado PASS/FAIL/NOT_RUN/UNAVAILABLE.

### T2 - Convenciones y naming
- auditoria read-only;
- convencion por capa;
- impacto/imports;
- plan de normalizacion;
- aplicar solo despues de validation baseline suficiente.

### T3 - Project Index v1

Estado: experimental / en desarrollo.

- `project-index.toml` versionado;
- `.index/` como output derivado;
- discovery y exclusions;
- manifest + hashes;
- revision Git;
- AST / symbols;
- imports / relations;
- busqueda textual;
- query CLI local;
- incremental indexing;
- benchmark con consultas reales de FitFlow.

La semántica con embeddings es opcional y debe justificarse mediante medición.

El Context Bundle definitivo no se congela durante esta etapa.
Se registrarán únicamente los requisitos observados durante el uso real.

#### T4 - Context delivery para Codex

Después de estabilizar Project Index y Codex:

1. utilizar primero consultas CLI/locales;
2. estudiar una Skill si el workflow se vuelve repetitivo;
3. formalizar Context Bundle v1 al estabilizar el MVP;
4. evaluar MCP solamente después.

No adoptar una interfaz más compleja antes de demostrar la necesidad.

### T5 - AiderDesk local pipeline
M-Explorer -> Worker -> Reviewer, desarrollado sin bloquear el producto.

### T6 - MCP (estudio futuro)
Evaluar MCP como interfaz estandar para exponer Project Index u otras herramientas a Codex. No implementar hasta tener Codex funcional y el indice suficientemente estable.

### T7 - Orquestacion futura
Symphony u otras formas de dispatch pueden estudiarse cuando Jira/tasks/validation ya funcionen de forma natural con humano en control.

## 4. Arquitectura objetivo

Monolito modular incremental y probado. No microservicios, Kafka/RabbitMQ, CQRS o event sourcing para necesidades actuales del MVP.

## 5. Autonomia

Agentes pueden explorar, implementar cambios acotados y ejecutar validaciones dentro del scope.

Decision humana explicita para:
- dominio/arquitectura;
- dependencias base;
- migraciones destructivas;
- seguridad transversal;
- ampliar MVP;
- superseder ADRs;
- integrar cambios con riesgo no validado.

## 6. Jira

Jira organiza el trabajo, no redefine la arquitectura.

Dimensiones estables:
- status;
- area;
- execution lane;
- task type;
- priority;
- epic/milestone;
- labels excepcionales.

No automatizar por automatizar. Primero estabilizar el flujo manual y luego estudiar automatizaciones que reduzcan cambios repetitivos sin quitar el control humano.

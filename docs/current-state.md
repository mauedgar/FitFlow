# Estado actual de FitFlow

**Snapshot documental:** 2026-08-13  
**Milestone de producto:** Sprint 6.8 - en desarrollo  
**Objetivo inmediato:** estabilizar el nucleo y cerrar el backend suficiente para avanzar al MVP.

## 1. Estado general

Sprint 6.8 sigue abierto. Su funcion es consolidar dominio, tipado, contratos, relaciones, responsabilidades y endpoints necesarios sin iniciar otra refactorizacion indefinida.

El frontend existe, pero no se considera actualmente una representacion fiable del flujo completo hasta sincronizarlo con contratos backend estabilizados.

## 2. Backend

### Confirmado / avanzado
- FastAPI async, SQLAlchemy 2.x Async, Pydantic v2, PostgreSQL, JWT y Redis forman el stack vigente.
- Router / Schema / Service / CRUD / Model sigue siendo la base arquitectonica.
- Booking dispone de una estrategia de creacion con chequeo atomico de capacidad/duplicados que debe preservarse y validarse.
- cancelacion operacional != eliminacion logica.
- ClassSession utiliza capacidad snapshot/disponibilidad derivada.
- existen vistas/schemas de Front Desk sobre el dominio existente.

### En consolidacion / a verificar
- relaciones/cardinalidades y tipado SQLAlchemy;
- eliminacion de ignores que oculten problemas reales;
- contratos Pydantic Create/Update/Public/Internal;
- endpoints y errores HTTP;
- cobertura de tests critica;
- auditoria temporal/actor;
- convenciones de naming del repositorio.

## 3. ClassSchedule / RRULE

RRULE es una **decision aceptada de arquitectura objetivo**, no una implementacion asumida.

Sprint 6.8 debe verificar/completar:
- contrato RRULE;
- generacion de sesiones;
- eliminacion de fallbacks legacy incompatibles;
- ventana de vigencia;
- capacidad snapshot;
- conflictos de profesor;
- tests correspondientes.

## 4. Testing

### Baseline estructural v3
La documentacion adopta una estructura de `backend/tests/` con:
- smoke;
- unit;
- integration;
- api;
- concurrency;
- helpers/factories;
- templates no recolectables por pytest.

Se incluye `backend/pytest.ini`, un smoke test del harness y wrappers de ejecucion.

### Estado real de cobertura
**Pendiente critico.** La existencia del harness no significa que el dominio este cubierto. La primera task operativa debe reconciliar dependencias/fixtures con el backend real e incorporar tests representativos de Booking y demas invariantes criticas.

Hasta entonces, la automatizacion debe distinguir claramente `PASS`, `FAIL`, `NOT_RUN` y `UNAVAILABLE`.

## 5. Frontend

Stack: React + TypeScript + Vite + Chakra UI + TanStack Query + Axios.

Estado: existente pero parcialmente desacoplado del backend actual. No se prioriza rediseño visual; la proxima integracion se apoya en contratos estabilizados.

## 6. Infraestructura

- Docker + Docker Compose;
- PostgreSQL;
- Adminer para desarrollo/administracion;
- Redis segun configuracion.

No introducir brokers/microservicios para el MVP.

## 7. Operacion de desarrollo

Se adopta un ciclo de task comun para humano/Codex/Aider:
- Jira: control de trabajo;
- Git: trazabilidad de implementacion;
- `.ai/tasks/`: contrato, plan/estado cuando aplique y resultado;
- `docs/`: conocimiento durable.

Estados de referencia: Backlog -> Ready -> In Progress -> Validation -> Review -> Done, con Blocked.

## 8. Tooling de IA

### Codex + Project Index
Direccion principal para tareas complejas. El indice localiza; Codex verifica fuente real.

### Project Index
Diseno avanzado / implementacion progresiva. Discovery + AST + relaciones + docs; semantica opcional por medicion.

### AiderDesk
Rama operativa experimental. M-Explorer util para localizar evidencia; Worker/Reviewer permanecen separados.

EmbeddingGemma no es requisito de M-Explorer.

## 9. Secuencia inmediata de consolidación

El próximo bloque de Sprint 6.8 se ejecutará mediante tareas delimitadas:

1. **Testing baseline operativo**
   - hacer pytest/pytest-asyncio ejecutable contra el backend real;
   - establecer fixtures seguras;
   - comenzar por invariantes críticas.

2. **Naming audit read-only**
   - inventariar convenciones por capa;
   - no renombrar todavía.

3. **SQLAlchemy 2.x model normalization**
   - normalizar sintaxis y typing;
   - preservar atributos, constraints, relaciones y semántica actuales.

4. **ORM integrity review**
   - revisar FK, relationships, cardinalidad, cascade, nullable, unique e índices;
   - separar diagnóstico de corrección;
   - cambios ambiguos requieren decisión humana.

5. **Domain enums & states alignment**
   - inventariar enums y strings operativos;
   - reconciliar roles, status, plans, activity y difficulty;
   - resolver explícitamente `ClassSessionStatus.draft` y `AllowedPlan`.

6. **Pydantic v2 contract alignment**
   - consolidar Create / Update / Public / Internal;
   - mantener reglas estructurales separadas de reglas de negocio.

7. **ClassSchedule / ClassSession consolidation**
   - verificar e implementar RRULE según la decisión aceptada;
   - generación de sesiones;
   - temporalidad;
   - capacity_snapshot;
   - allowed_plan;
   - tests correspondientes.

Después de este bloque se continuará con Booking, Front Desk y cierre de endpoints.

## 10. Documentos reemplazados

Sprint 7 antiguo y los roadmaps/indexador originales permanecen archivados. Esta suite v3 pasa a ser baseline documental cuando se incorpora al repositorio.

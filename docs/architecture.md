# Arquitectura de FitFlow

**Estado:** Canonico

**Actualizado:** 2026-08-15

## 1. Proposito

Definir la arquitectura vigente, las responsabilidades obligatorias, la
direccion de dependencias y la evolucion aprobada de FitFlow.

Este documento es normativo. El estado de implementacion se registra en
`current-state.md`; las tareas y sus resultados no modifican esta arquitectura.

## 2. Baseline tecnologico

### Backend

- Python 3.11+
- FastAPI async
- SQLAlchemy 2.x Async
- Alembic
- Pydantic v2
- PostgreSQL
- Redis
- JWT access y refresh con roles

### Frontend

- React
- TypeScript
- Vite
- Chakra UI
- TanStack Query
- Axios

### Desarrollo e infraestructura

- Docker y Docker Compose
- PostgreSQL
- Adminer
- Redis cuando el entorno lo requiera

Adminer es tooling de desarrollo y no forma parte del dominio.

## 3. Arquitectura vigente

FitFlow es un monolito full-stack. El backend esta organizado fisicamente por
capas tecnicas y logicamente por dominios representados en cada capa.

```text
app/
  routers/
  services/
  crud/
  schemas/
  db/models/
```

La direccion obligatoria de dependencias es:

```text
Router -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL
```

Los schemas Pydantic son contratos de entrada y salida. No constituyen una capa
de persistencia ni una etapa fija entre las capas anteriores.

### Flujo de entrada

```text
HTTP Request
  -> FastAPI: routing, dependencias y validacion
  -> Router
  -> Service
  -> CRUD
  -> SQLAlchemy Model
  -> PostgreSQL
```

### Flujo de salida

```text
PostgreSQL
  -> SQLAlchemy Model
  -> CRUD
  -> Service
  -> Router
  -> Pydantic response model
  -> JSON
```

## 4. Responsabilidades obligatorias
### Docstrings
Las reglas de estilo, docstrings, linting y type checking se definen en `quality-and-validation.md` o `coding-standards.md`.
### Routers / FastAPI

Los routers son responsables de:

- protocolo HTTP;
- parametros de path, query y body;
- dependency injection;
- autenticacion y autorizacion;
- status codes y OpenAPI;
- traduccion de errores de dominio a respuestas HTTP;
- declaracion del contrato de respuesta.

Los routers no contienen reglas de negocio ni consultas ORM. El codigo nuevo
debe delegar los casos de uso en services.

### Schemas / Pydantic v2

Los schemas son responsables de:

- contratos de entrada y salida;
- tipos y serializacion;
- validacion estructural;
- invariantes locales que no requieren estado persistido.

Los schemas no consultan infraestructura, no acceden a ORM y no deciden reglas
de negocio dependientes del estado.

Convenciones vigentes:

- `*InResponse`: contrato compacto para una respuesta anidada;
- `*Public`: contrato publico y autocontenido;
- `<Class1>In<Class2>Response`: contrato compacto de `Class1` dentro de
  `Class2`;
- `<Class>WithRelations`: contrato que requiere relaciones ORM cargadas
  explicitamente;
- `*_refs.py`: contratos hoja destinados a evitar ciclos entre schemas.

Los modulos `*_refs.py` no importan services, CRUD ni modelos ORM.

### Services

Los services son responsables de:

- casos de uso;
- reglas de negocio;
- calculos de dominio;
- validaciones dependientes del estado;
- coordinacion entre operaciones CRUD;
- transformaciones puras y resultados derivados.

Una funcion service es `async` solo cuando coordina I/O. Los helpers que operan
exclusivamente sobre datos ya cargados son sync.

El codigo nuevo de services no ejecuta `select`, `db.execute`, `db.scalar`,
`db.add` ni consultas ORM equivalentes. Las operaciones de almacenamiento se
delegan en CRUD.

### CRUD

CRUD es responsable de:

- consultas SQLAlchemy;
- carga explicita de relaciones;
- filtros de persistencia;
- altas, modificaciones y bajas;
- operaciones atomicas;
- control transaccional de operaciones de almacenamiento.

CRUD puede implementar operaciones especificas cuando una garantia de
consistencia depende de la base de datos. CRUD no importa routers, services ni
schemas de respuesta y no define politicas comerciales.

### SQLAlchemy / PostgreSQL

Los modelos ORM representan persistencia, relaciones y restricciones
estructurales. No importan routers, services, CRUD ni schemas Pydantic.

PostgreSQL es la fuente persistente del dominio.

### Redis

Redis mantiene estado temporal o de infraestructura con ownership explicito.
No reemplaza ni duplica a PostgreSQL como fuente persistente del dominio.

## 5. Politica de dependencias

Dependencias permitidas:

| Origen | Destinos permitidos |
| --- | --- |
| Router | Services, schemas, dependencias HTTP y seguridad |
| Service | CRUD, dominio, enums y schemas cuando produce un DTO derivado |
| CRUD | Modelos ORM, sesion DB y utilidades de persistencia |
| Schema | Schemas hoja, tipos y enums estables |
| Modelo ORM | Base ORM, mixins, tipos y enums estables |

Dependencias prohibidas:

- CRUD hacia services o routers;
- modelos ORM hacia schemas, CRUD, services o routers;
- schemas hacia CRUD, services o modelos ORM;
- imports mutuos entre services;
- imports locales usados como solucion permanente a ciclos arquitectonicos.

`TYPE_CHECKING` se utiliza solo para anotaciones que no se necesitan en runtime.
No se utiliza para ocultar una dependencia circular funcional.

## 6. Estado de transicion

Se reconocen como deuda arquitectonica vigente:

- routers que llaman CRUD directamente;
- services que ejecutan consultas o persistencia ORM directa;
- organizacion interna inconsistente de algunos routers;
- contratos HTTP pendientes de validacion integral.

Estas desviaciones pueden conservarse hasta que una tarea delimitada las
refactorice. No constituyen precedente para codigo nuevo.

Los mappers `to_*` son validos cuando son transformaciones puras. No realizan
I/O ni carga implicita de relaciones. Deben eliminarse cuando Pydantic pueda
serializar directamente el ORM cargado sin perder campos derivados ni reglas
del contrato.

## 7. Arquitectura objetivo: monolito modular

FitFlow evolucionara gradualmente a un monolito modular sin alterar su unidad
de despliegue.

La arquitectura objetivo exige:

- limites claros por dominio;
- cohesion interna de cada dominio;
- dependencias explicitas entre dominios;
- ausencia de acceso transversal directo a persistencia ajena;
- contratos HTTP estables;
- PostgreSQL compartido como fuente persistente;
- una aplicacion backend desplegable como unidad.

La estructura fisica por capas se conserva durante el MVP. La reorganizacion
por modulos verticales solo se realiza mediante una decision arquitectonica y
una migracion planificada.

No se incorporan microservicios, brokers, CQRS ni event sourcing sin una
necesidad aprobada de escala, ownership o aislamiento.

## 8. Dominio operativo

```text
User -> Person -> Client / Teacher
Client -> Membership
GymClass -> ClassSchedule -> ClassSession -> Booking
```

Front Desk es una capacidad operativa sobre el dominio existente y no una
entidad paralela.

## 9. Concerns transversales

### Seguridad

JWT, roles y dependencias de usuario actual permanecen centralizados y
auditables.

### Fechas

La interpretacion operacional de horarios pertenece a services. Los horarios
locales se convierten a UTC en limites definidos y se persisten de forma
consistente.

### Auditoria

Los timestamps y estados existentes proporcionan la trazabilidad vigente. La
auditoria uniforme por actor queda pendiente de una politica, modelo de datos y
migracion aprobados. No se agregan parametros `created_by` aislados antes de
esa decision.

### Soft delete

`active`, estados operativos y `deleted_at` representan conceptos diferentes.
La baja logica no reemplaza las transiciones de estado.

### Testing

La estrategia de testing forma parte de la arquitectura operativa. Las
validaciones obligatorias se definen en `quality-and-validation.md`.

## 10. Tooling de IA

Las herramientas de IA son tooling de desarrollo. Sus indices y caches son
artefactos derivados y no reemplazan codigo, tests ni documentacion canonica.

## 11. Ownership documental

- `architecture.md`: arquitectura, responsabilidades y dependencias;
- `current-state.md`: estado implementado y desviaciones verificadas;
- `quality-and-validation.md`: estrategia y comandos de validacion;
- `TASK.md`: alcance autorizado de una tarea;
- `RESULT.md`: resultado y evidencia de ejecucion.

Un informe, prompt o resultado de agente no modifica esta arquitectura. Todo
cambio arquitectonico debe actualizar este documento de forma explicita.

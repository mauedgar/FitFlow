# Arquitectura de FitFlow

**Estado:** Canonico  
**Actualizado:** 2026-08-13

## 1. Proposito

Documentar la arquitectura actual, las responsabilidades obligatorias y la direccion objetivo sin confundir target con implementacion.

## 2. Baseline actual

FitFlow es un repositorio full-stack.

### Backend
- Python 3.11+
- FastAPI async
- SQLAlchemy 2.x Async
- Alembic
- Pydantic v2
- PostgreSQL
- Redis
- JWT access + refresh y roles

### Frontend
- React
- TypeScript
- Vite
- Chakra UI
- TanStack Query
- Axios

### Infraestructura de desarrollo
- Docker
- Docker Compose
- PostgreSQL
- Adminer
- Redis cuando el entorno lo requiera

Adminer es una herramienta de administracion/desarrollo, no parte del dominio.

## 3. Flujo de responsabilidades

```text
Request
  -> Pydantic Schema
  -> Router
  -> Service
  -> CRUD
  -> SQLAlchemy Model
  -> PostgreSQL
```

### Routers / FastAPI
HTTP, parametros, DI, autenticacion/autorizacion, status codes, OpenAPI y traduccion de errores. No son propietarios de reglas de negocio.

### Schemas / Pydantic v2
Contratos, tipos, serializacion y validacion estructural. Pueden expresar invariantes del dato; no deben consultar DB ni decidir acceso de negocio.

### Services
Propietarios de reglas de negocio, calculos, validaciones dependientes de estado y orquestacion.

### CRUD
Acceso a datos, consultas, persistencia y operaciones transaccionales. Puede garantizar consistencia atomica; no define politicas comerciales.

### SQLAlchemy / PostgreSQL
Persistencia, relaciones e integridad estructural.

### Redis
Estado temporal/infraestructura con ownership explicito. No duplica a PostgreSQL como fuente persistente del dominio.

## 4. Postura arquitectonica conocida

### Confirmado
- separacion Router / Schema / Service / CRUD / Model;
- SQLAlchemy 2.x + Pydantic v2;
- PostgreSQL como persistencia principal;
- frontend React/TypeScript/Vite/Chakra/TanStack/Axios;
- Booking requiere proteccion transaccional de capacidad/duplicados;
- estados operativos se distinguen de eliminacion logica;
- el workflow de desarrollo se apoya en Git, tareas delimitadas y validacion reproducible.

### Accepted / Pending Implementation
- RRULE como fuente unica de recurrencia de `ClassSchedule`;
- eliminacion definitiva del legacy equivalente a `days_of_week`;
- consolidacion gradual hacia monolito modular;
- baseline completo de tests de negocio/integracion suficiente para automatizacion confiable.

## 5. Arquitectura objetivo: monolito modular

FitFlow se consolidara gradualmente como **Modular Monolith**.

Esto significa:
- una aplicacion sencilla de desarrollar/desplegar;
- limites internos claros por responsabilidades y dominio;
- sin microservicios, brokers, CQRS o event sourcing para resolver necesidades actuales del MVP;
- posibilidad futura de extraer un modulo si aparece una necesidad real de escala, ownership o aislamiento.

No son "beneficios del monolito" sino tecnicas alternativas que agregarian complejidad distribuida innecesaria hoy.

Una futura extraccion a servicios no sera gratuita: requerira contratos de comunicacion, ownership de datos, seguridad entre servicios, observabilidad, deploy y testing independiente. La modularidad interna reduce el costo de esa evolucion, no lo elimina.

## 6. Dominio operativo

```text
User -> Person -> Client / Teacher
Client -> Membership
GymClass -> ClassSchedule -> ClassSession -> Booking
```

Front Desk es una vista/operacion sobre el dominio existente, no una entidad paralela.

## 7. Concerns transversales

### Seguridad
JWT, roles y current-user dependencies deben permanecer centralizados y auditables.

### Fechas
La interpretacion operacional de horarios pertenece a services. Evitar mezclar hora local y UTC arbitrariamente.

### Auditoria
Timestamps/actor donde aporten trazabilidad. No introducir event sourcing universal para el MVP.

### Soft delete
`active`, `status` y `deleted_at` expresan conceptos distintos.

### Testing
La estrategia de testing es parte de la arquitectura operativa: las capas deben ser testeables sin requerir que el agente reinterprete todo el sistema en cada cambio. Ver `quality-and-validation.md`.

## 8. Tooling de IA

Las herramientas de IA son tooling de desarrollo:
- Codex como pipeline potente;
- Project Index reutilizable;
- AiderDesk como pipeline local independiente;
- RepoMap como hint runtime de Aider;
- MCP como candidato futuro de interfaz para exponer tools/contexto, no requisito actual.

Indices/caches son derivados y nunca reemplazan al codigo.

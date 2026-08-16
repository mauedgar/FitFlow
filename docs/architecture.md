---
document_id: FF-ARCH-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Arquitectura de FitFlow

## Alcance

Este documento define la arquitectura del producto. La plataforma de asistencia
vive en el repositorio hermano `FitFlow-ai` y no puede introducir dependencias
runtime en FitFlow sin ADR y aprobación humana.

## Baseline

| Área | Tecnologías vigentes |
| --- | --- |
| Backend | Python 3.11+, FastAPI async, SQLAlchemy 2.x Async, Alembic, Pydantic v2, PostgreSQL, JWT, Redis |
| Frontend | React, TypeScript, Vite, Chakra UI, TanStack Query, Axios |
| Entorno | Docker, Docker Compose, PostgreSQL, Adminer; Redis cuando corresponda |

Adminer es tooling de desarrollo. Redis no reemplaza a PostgreSQL como fuente
persistente.

## Arquitectura vigente

FitFlow es un monolito full-stack. El backend se organiza físicamente por capas
técnicas y lógicamente por dominios:

```text
backend/app/
  routers/
  services/
  crud/
  schemas/
  db/models/
```

Dirección obligatoria:

```text
HTTP -> Router -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL
```

Los schemas Pydantic validan y serializan contratos de entrada/salida. No son
una capa lineal de persistencia.

## Ownership por capa

| Capa | Debe hacer | No debe hacer |
| --- | --- | --- |
| Router | HTTP, DI, auth, status, OpenAPI, traducción de errores | reglas de negocio o consultas ORM |
| Schema | tipos, validación estructural e invariantes locales | I/O, ORM o decisiones con estado persistido |
| Service | caso de uso, reglas, coordinación y transformaciones puras | SQLAlchemy directo en código nuevo |
| CRUD | consultas, cargas, persistencia, atomicidad y locks | política comercial o dependencias hacia router/service |
| Modelo ORM | estructura persistente, relaciones y constraints | importar schemas, CRUD, services o routers |

Un service es `async` solo cuando coordina I/O. Un mapper `to_*` es válido si es
puro y no dispara carga implícita.

## Dependencias

| Origen | Destinos permitidos |
| --- | --- |
| Router | services, schemas, dependencias HTTP y seguridad |
| Service | CRUD, dominio, enums y DTO necesarios |
| CRUD | modelos ORM, sesión DB y utilidades de persistencia |
| Schema | schemas hoja, tipos y enums estables |
| Modelo | base ORM, mixins, tipos y enums estables |

Se prohíben ciclos funcionales, imports locales permanentes para ocultarlos y
`TYPE_CHECKING` usado para evadir una dependencia runtime incorrecta.

## Deuda reconocida

- routers heredados que llaman CRUD directamente;
- services heredados con operaciones ORM;
- organización inconsistente en algunos routers;
- cobertura HTTP integral pendiente.

La deuda no constituye precedente. Cada refactor requiere tarea y evidencia.

## Objetivo

Evolución gradual a monolito modular, manteniendo una unidad de despliegue,
límites explícitos y PostgreSQL compartido. No incorporar microservicios,
brokers, CQRS o event sourcing sin necesidad aprobada.

## Frontera con FitFlow-ai

`FitFlow-ai` puede leer código y producir artefactos derivados. No es una
dependencia del runtime del producto. Sus outputs son regenerables y se guardan
fuera de `FitFlow`, salvo contratos/prompts versionados en `.ai/`.

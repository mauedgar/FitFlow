---
document_id: FF-AI-REGISTRIES-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-18
---

# Registries vNext

## Role Registry

Define autoridad, inputs/outputs, tools permitidas, escritura, riesgos y
escalamiento. No contiene runtime IDs de modelos.

## Skill Registry

Define origen, version/pin, permisos, roles permitidos, contratos de entrada y
salida, determinismo y estado `adopted|evaluate|planned|rejected`.

## Model Registry

Define `provider`, `runtime_id`, disponibilidad, trust, quota pool,
capabilities, latencia, contexto, criticality ceiling, roles preferidos,
prohibiciones, benchmark status y ultima verificacion. Un nombre comercial sin
runtime ID verificado no es una entrada activa.

## Workflow Registry

Enumera workflows habilitados, estados, transitions, retry policy, gates,
feature flags y schemas. El codigo TypeScript es la especificacion ejecutable;
el registro descubre y versiona esa implementacion.

## Run Registry

Indexa `run_id`, `task_id`, baseline, workflow, eventos, artefactos, context
delivery, modelos, uso, retries y estado terminal. Se deriva de los artefactos
durables; SQLite es una proyeccion local.

## Regla de cambio

Los registries son datos versionados. Cambiar autoridad, criticality ceiling,
permisos o estados requiere review independiente y aceptacion del desarrollador.

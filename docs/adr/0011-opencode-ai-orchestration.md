---
document_id: FF-ADR-0011
status: superseded
machine_context: true
superseded_by: FF-ADR-0014
---

# ADR 0011: Codebase como superficie de orquestación de IA

- **Estado:** Superseded por ADR 0014
- **Fecha:** 2026-08-16
- **Supersede:** ADR 0007
- **Amend:** ADR 0008

## Contexto

La operación anterior separaba herramientas y duplicaba prompts, routing y
estado. Se requiere un flujo completo, auditable y capaz de usar proveedores y
modelos locales sin alterar los contratos de trabajo.

## Decisión

Codebase será la superficie final de orquestación. La integración se realiza
mediante un adaptador que traduce configuración y prompts, mientras FitFlow
conserva contratos neutrales en `.ai/`.

Aider queda descartado y no constituye lane, fallback ni dependencia.

Roles activos:

- Orchestrator;
- Planner/Audit;
- Explorer;
- Coder A;
- Coder B;
- Reviewer;
- Validator.

Flujo:

`PLAN -> EXPLORE -> EXECUTE -> REVIEW -> VALIDATE -> PENDING_ACCEPTANCE`.

El desarrollador aprueba arquitectura, riesgo alto, dependencias, seguridad,
migraciones destructivas, promoción documental y `DONE`.

## Reglas

- Cada ejecución registra rol, proveedor, modelo, nivel de razonamiento,
  baseline y outputs.
- Los modelos se asignan por capacidad medida, no por marca fija.
- Reviewer no puede ser la misma ejecución que Coder.
- Riesgo alto queda bloqueado.
- Solo se paralelizan ownership keys disjuntas.
- El adaptador no puede reducir gates ni autoridad del desarrollador.

## Consecuencias

Se obtiene un único ciclo de vida y se mantienen modelos intercambiables. La
primera versión exige configuración manual y evaluación antes de automatizar
dispatch, hooks o MCP.

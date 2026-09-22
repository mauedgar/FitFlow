---
document_id: FF-ADR-0018
status: accepted
machine_context: true
version: 1.0
updated: 2026-08-19
supersedes: []
---

# ADR 0018: Entorno Python gestionado con uv

## Decision

Sustituir `pip` por `uv` para la creacion y gestion de entornos Python. El
entorno de herramientas externo se resuelve desde el root explicito de
Tecnotron-ai declarado por Project Profile, no por adyacencia de directorios.

`uv` versiona el interpretador (CPython 3.12.11), crea el venv de forma
determinista y reproduce dependencias de forma reproducible.

## Contexto

- El venv anterior vivia en `scripts/.venv_tools` del repo FitFlow, creado con
  `python -m venv` y gestionado con `pip`.
- Los hooks `pre-commit` y `commit-msg` referenciaban `bin/activate` (path
  Linux) y fallaban en Windows; ademas faltaba `black`, usado por el hook.
- Tecnotron-ai es el repositorio externo del sistema de desarrollo; la doctrina
  separa herramienta de producto y resuelve su root de forma explicita.

## Consecuencias

- El venv de herramientas permanece fuera del repo FitFlow y se resuelve desde
  el root externo configurado en Project Profile.
- Hooks y referencias usan `Scripts/activate` y la ruta externa resuelta; no
  infieren un directorio hermano por nombre.
- `networkx`, `black` y el resto de paquetes del venv anterior se replican con
  `uv pip install -r requirements` (110 paquetes).
- `scripts/.venv_tools` queda eliminado de FitFlow.
- Instalaciones futuras de dependencias Python requieren decision explicita del
  desarrollador y se ejecutan con `uv`.
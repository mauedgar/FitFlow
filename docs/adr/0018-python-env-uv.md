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

Sustituir `pip` por `uv` para la creacion y gestion de entornos Python, y
relocalizar el venv de herramientas a `FitFlow-ai/python/.venv_tools`.

`uv` versiona el interpretador (CPython 3.12.11), crea el venv de forma
determinista y reproduce dependencias de forma reproducible.

## Contexto

- El venv anterior vivia en `scripts/.venv_tools` del repo FitFlow, creado con
  `python -m venv` y gestionado con `pip`.
- Los hooks `pre-commit` y `commit-msg` referenciaban `bin/activate` (path
  Linux) y fallaban en Windows; ademas faltaba `black`, usado por el hook.
- FitFlow-ai es la carpeta hermana y canonical del AI Core; la doctrina pedia
  separar herramienta de producto.

## Consecuencias

- El venv pasa a `../FitFlow-ai/python/.venv_tools` (fuera del repo FitFlow).
- Hooks y referencias usan `Scripts/activate` y la ruta absoluta de la hermana.
- `networkx`, `black` y el resto de paquetes del venv anterior se replican con
  `uv pip install -r requirements` (110 paquetes).
- `scripts/.venv_tools` queda eliminado de FitFlow.
- Instalaciones futuras de dependencias Python requieren decision explicita del
  desarrollador y se ejecutan con `uv`.
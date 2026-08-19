---
document_id: FF-STATE-001
status: canonical
machine_context: true
version: 5.0
snapshot: 2026-08-18
---

# Estado actual de FitFlow

## Producto confirmado

- Sprint 6.8 consolidado hasta `FF-LOCAL-010`.
- Backend con FastAPI async, SQLAlchemy 2.x Async, Pydantic v2 y PostgreSQL.
- RRULE es la unica fuente de recurrencia; genera faltantes futuros en horizonte
  de 15 dias y persiste sesiones en UTC.
- Booking admite resolucion por sesion o agenda, protege capacidad, conserva
  cancelaciones y no cuenta reservas canceladas como cupo.
- ClassSession conserva soft delete administrativo e historia.
- Front Desk usa un service unico y check-in `confirmed -> attended` con
  `checked_in_at`.
- La arquitectura objetivo del producto continua siendo monolito modular por
  bounded contexts, con migracion gradual y fitness functions.

## Validacion confirmada

- Harness en `backend/tests/` y base exclusiva `fitflow_test`.
- Pruebas dirigidas de metadata, mappers, RRULE, Booking, cancelacion,
  capacidad, check-in y Redis.
- Ruff y Pyright existen en la imagen de tests.
- La suite HTTP integral del MVP no esta demostrada.

## Plataforma de asistencia IA

Estado global: `BASELINE_ACCEPTED`.

- `FF-AI-VNEXT-001` aceptada; `FF-AI-VNEXT-002` (doctor) implementado y en
  `PENDING_ACCEPTANCE`. `ffai doctor` reporta el toolchain en JSON v2 sin
  installs: node, npm, python, git, gh, openspec, repomix y opencode
  `AVAILABLE`; repo-packager y project-profile operativos; LibreOffice
  `UNREACHABLE` sin soffice en PATH.
- `FF-AI-VNEXT-003` (contracts v2 Zod + registries loaders) y
  `FF-AI-VNEXT-004` (State Machine + Run Store) implementados y en
  `PENDING_ACCEPTANCE`; tests 24/24 PASS en `../FitFlow-ai`.
- OpenCode CLI `1.18.18` es la superficie automatizada elegida; Desktop queda
  para uso manual del desarrollador. El adapter vNext y su conformance suite no
  estan implementados.
- Repomix `1.18.0` esta disponible. `repo-packager` genera paquetes, pero su
  contrato vNext y sus fallos de exclusion/seleccion aun requieren correccion
  (`FF-AI-VNEXT-006`, pausado).
- Node `22.18.0`, OpenSpec `1.9.0` y GitHub CLI `2.97.0` estan disponibles;
  GitHub esta autenticado. El root OpenSpec y los adapters permanecen pending.
- `FitFlow-ai` vive como carpeta hermana en `../FitFlow-ai/` (repo propio en
  preparacion). AI Core lee registries y contractos de `../FitFlow/.ai/`.
- OpenCode descubrio runtime IDs de FastContext, Qwen y DeepSeek en LM Studio;
  inferencia, benchmark y rol efectivo quedan `UNVERIFIED`.
- GitHub Copilot queda deferred y fuera del acceso programatico. El
  desarrollador es intermediario de cualquier orden manual.
- LibreOffice `26.2.5.2` convierte DOCX correctamente cuando `soffice` y Poppler
  se agregan al PATH del proceso.
- LlamaIndex, Qdrant, embeddings, Promptfoo, MCP y Temporal son posteriores a
  gates explicitos; no se declaran funcionales.
- `scripts/.venv_tools` es un entorno local reutilizable para discovery, no el
  entorno oficial de FitFlow-ai.

## Deuda activa

- cobertura API integral y fixtures HTTP async compartidas;
- refactors de fronteras heredadas;
- implementar contracts y registries v2;
- corregir y medir `repo-packager` (pausado) antes del Agent MVP;
- implementar State Machine, persistencia de run y FinOps-as-Code;
- verificar adapter OpenCode, GitHub/OpenSpec y modelo Explorer;
- medir contexto, calidad y retrabajo antes de ampliar autonomia.

# Prompt - Configurar Codex para FitFlow

Quiero configurar Codex como pipeline principal de desarrollo para mi repositorio FitFlow.

Contexto del proyecto:
- Windows.
- Root esperado: `C:\Proyectos Web\FitFlow`.
- Backend Python 3.11+ / FastAPI async / SQLAlchemy 2.x Async / Alembic / Pydantic v2 / PostgreSQL / Redis / JWT.
- Frontend React + TypeScript + Vite + Chakra UI + TanStack Query + Axios.
- Arquitectura actual por responsabilidades: Router -> Schema -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL.
- Target: monolito modular incremental, sin microservicios para el MVP.
- Milestone actual: Sprint 6.8; objetivo posterior: MVP operativo.
- El repositorio tendra `AGENTS.md`, `docs/`, `.ai/` y `backend/tests/`.
- Jira controla tareas; Git conserva implementacion; `.ai/tasks/` contiene TASK/PLAN/STATUS/RESULT.
- AiderDesk existe como pipeline local separado; no debe interferir con Codex.
- Project Index es un tooling futuro/progresivo para recuperar contexto reutilizable.
- Pytest es un prerequisito critico para automatizacion fiable.

Necesito que uses SOLO documentacion oficial actual de OpenAI para cualquier afirmacion sobre Codex.

Objetivo de esta sesion:
1. Identificar la forma recomendada de usar Codex en este repositorio (CLI/app/worktrees/config segun lo disponible).
2. Revisar como Codex descubre y aplica `AGENTS.md`.
3. Definir permisos/sandbox adecuados para una primera etapa segura.
4. Definir como usar Plan mode para tareas complejas sin implementar automaticamente.
5. Definir como aislar tasks con Git/worktrees cuando sea necesario.
6. Verificar como se manejan archivos ignorados y que no existe una supuesta configuracion inventada.
7. Alinear los comandos de validacion con `backend/tests/`.
8. Proponer una configuracion minima: no quiero instalar plugins, MCP, subagentes ni automatizacion hasta que Codex basico funcione.
9. Darme una prueba controlada inicial read-only y luego una task pequena de escritura.
10. Explicar limites/riesgos antes de recomendar cambios.

No modifiques el repositorio ni me des un setup gigante de una sola vez. Quiero configurar, probar y validar por capas.

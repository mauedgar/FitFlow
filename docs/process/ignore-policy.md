# Politica de exclusiones para Git, Aider e indexadores

## Git

`.gitignore` decide que artefactos locales no se versionan. No es una frontera de seguridad para un agente.


Exclusiones criticas:
- `backend/.venv_backend/`
- `scripts/.venv_tools/`
- `.ai/local/`
- `.index/` / `index/`
- caches/test outputs
- secretos `.env*`

## Aider

Aider usa `.aiderignore`. El baseline excluye dependencias, virtualenvs, historico documental, logs locales e indice derivado.

Para experimentos backend-only se incluye `.aiderignore.backend`.

## Codex

No se define un `.codexignore` inventado. Mantener `AGENTS.md` compacto, usar Git/worktree/sandbox/configuracion oficial y no asumir que `.gitignore` impide a Codex leer un archivo presente en el workspace.

## Project Index

Debe aplicar su propia lista de exclusiones, alineada con estas reglas, y registrar que paths fueron ignorados en su snapshot.

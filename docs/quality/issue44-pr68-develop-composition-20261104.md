---
document_id: FF-ISSUE44-COMPOSITION-PR68-DEVELOP-20261104-001
status: draft_unaccepted
date: 2026-11-04
product_effect: candidate_only
acceptance: not_granted
---

# FitFlow — integración candidata aislada de normalización y seguridad

## Identidad y autoridad

- Repo: `mauedgar/FitFlow`. Rama base: `develop@55772398c72f4c1a41862dccd79b04d38016dfcb`, tree `ee59ccea9c4b6682a8ba0c739308b51214a8619d`.
- Fuente acumulativa: PR #68, commit `bfe89a705a20a8e99c87b54a5d38a628a44c95db`, tree `a6f597907788fec7b39b9e0faaf95ebc79f62aa8`. Su IR017 congelada: **0 findings, 3 advisories A10/A12/A13, NO_RECOMMEND**. Sus 6 workflows SUCCESS solo califican su propio SHA/tree.
- SOT v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`, no editada.
- Preflight diferencial: comparación desde `c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d` a PR68 da 194 rutas (140 modificadas, 54 agregadas, ninguna eliminada). Trees completos no truncados; sobre `develop` se reutilizan **blobs Git exactos** de esas 194 rutas. La única ruta común modificada por la línea reciente de `develop` es `backend/requirements_backend.txt`: prevalece la exportación completa generada por uv en PR68 para mantener coherencia con su manifiesto y lock.
- Se conservan todos los paths de `develop` no contenidos en el delta, particularmente `.github/dependabot.yml`, CI baseline, plantillas pasivas, DocImpact de PR #81 y `frontend/requirements_frontend.txt` corregido a UTF-8.

## Dependencias y límites

- `pyproject.toml`, `uv.lock`, `backend/requirements_backend.txt` y `backend/requirements_test.txt` se trasplantan **como conjunto atómico por SHA de blob**, desde el candidato acumulativo PR68. **No** se editan hashes a mano ni se mezclan con PR46 (cerrado sin merge).
- PR68 fija Python >=3.11,<3.14, asyncpg 0.32.0, pytest 9.2.0, pytest-asyncio 1.4.1, Ruff 0.17.3, Pyright 1.1.414, bcrypt nativo 4.3.0 sin Passlib. La generación original del lock/exports está registrada en https://github.com/mauedgar/FitFlow/actions/runs/41486665601; **no** se afirma generación nueva en esta composición.
- PR #48, #50 y #51 continúan como alternativas independientes, sin borrado ni reconocimiento automático de DoD.
- Esta rama/PR es exclusivamente un **candidato pendiente de CI exacta e IR independiente**. No implica aceptación, integración canónica, despliegue, cierre de Issue #44 ni 0 advisories.

## Validaciones obligatorias

1. Ejecutar CI original de la nueva identidad (SHA/tree); verificar `uv lock --check`, equivalencia exports y hashes, Python 3.11/3.12/3.13 + pytest/Alembic PG15/Redis7 aislado, Ruff/Pyright y frontend build/tests.
2. Confirmar que los cambios de `develop` (Dependabot, CI y UTF-8 frontend) subsisten sin regresión; verificar el conflicto deliberado del export backend.
3. Revisar seguridad auth, JWT, bcrypt legacy, privacidad y schema sobre el nuevo árbol; nueva IR WEB_INLINE independiente exacta.
4. **A10** inventario ACK y decisión de rollout; **A12** ingress externo, TLS/IP host y staging real; **A13** Redis histórico/TTL y cleanup requieren evidencia operativa y autorización específica. No convertir los tests sintéticos en PASS real, no mutar Redis/DB real.
5. Cualquier cambio posterior genera SHA/tree nuevos y requiere gates nuevos. Sin merges/cierres automáticos.

Referencias: https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6620949335 y https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6621035692.

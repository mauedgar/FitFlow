# FitFlow — FF-LOCALvNext-000 — Plan de curación y revalidación de baseline

**Estado:** PLANNING
**Baseline:** commit actual de `feat/FF-NEXT-000` (rebaseado sobre `develop` tras 1a)

---

## Objetivo
Establecer un baseline de verdad único y verificable para la rama `feat/FF-NEXT-000` mediante:
1. Unificar la rama con `develop` (1a) y remontar la BD local (1b) para eliminar deriva.
2. Revalidar ese baseline ejecutando validaciones reales (1c).
3. Curar las 10 tareas locales (FF-LOCAL-001 a FF-LOCAL-010) usando **solo** evidencia primaria: código, tests, migraciones, configuración y `RESULT.md` por tarea.
4. Producir un veredicto único por tarea y un veredicto global de baseline.

---

## Insumos autorizados
- Código, tests, configuración y migraciones verificadas (precedencia 1).
- `docs/SOURCE_OF_TRUTH.md` (precedencia 2).
- Documentación canónica y ADR aceptados (precedencia 3).
- GitHub Issues aprobadas o sus espejos locales `TASK.md` autorizados (precedencia 4).
- Artefactos de run asociados al baseline correcto (precedencia 5).
- Contexto derivado asociado al baseline correcto (precedencia 6).

**Nota:** Los informes previos que daban por ausentes `RESULT.md` quedan invalidados como gap tras confirmación del Developer 2026-08-23.

---

## Precondiciones bloqueantes
| # | Precondición | Estado | Detalle |
|---|--------------|--------|---------|
| 1a | Unificar `feat/FF-NEXT-000` con `develop` (rebase/merge) | **EN_CURSO** | Ordenado por Developer 2026-08-23; ejecutar antes de cualquier validación. |
| 1b | Remontar BD local al baseline unificado | **EN_CURSO** | Requiere `.env` raíz con `POSTGRES_PASSWORD` (creado provisionalmente por el Developer; eliminarlo o preservarlo post-merge es decisión suya). |
| 1c | Revalidar baseline tras 1a y 1b | **EN_CURSO** | Ejecutar validaciones reales (tests, migraciones, health-checks) sobre el estado unificado. |

---

## Decisiones registradas
| Tema | Decisión | Evidencia / Nota |
|------|----------|------------------|
| **RESULT.md verificados** | **RESUELTA** | `001-010` — El Developer confirmó 2026-08-23 que `RESULT.md` existe en cada carpeta de task; los informes previos que los daban por ausentes quedan invalidados como gap. Usarlos como evidencia primaria en Fase 3. |
| **Promoción a DONE** | **RESUELTA** | 2026-08-23: FF-LOCAL-003 y FF-LOCAL-006 quedan promovidas a DONE. La sincronización del frontmatter de ambos `TASK.md` se ejecutará durante la Fase 3 citando evidencia `ruta:línea` (no antes). |
| **Integridad de ADRs** | **DERIVADA** | Todas — Derivada al plan hermano `.ai/tasks/FF-LOCALvNext-001-adr-integrity/PLAN.md`. Ejecutar ese ciclo después de la Fase 3. |

---

## Relación PLAN–TASK
Los **PLAN** orientan y delimitan; las **unidades ejecutables** se materializan después en `TASK.md` espejo cuando el Developer las aprueba; un **PLAN** puede derivar **1..n TASK**; mientras no exista `TASK`, este **PLAN** es la guía operativa autorizada. **No se crean TASK en este ciclo.**

---

## Pasos de ejecución
| Paso | Acción | Responsable | Evidencia esperada |
|------|--------|-------------|---------------------|
| 1 | Ejecutar precondiciones 1a, 1b, 1c en orden | Developer / Agente | Log de rebase, migraciones aplicadas, tests pasando |
| 2 | Inventariar 10 tareas FF-LOCAL-001..010 con `RESULT.md` existente | Agente | Tabla: Task | RESULT.md existe | Última modificación |
| 3 | Curar cada tarea: leer código/tests/migraciones/config + `RESULT.md`; emitir veredicto `PASS/FAIL/NOT_RUN/UNAVAILABLE/BLOCKED/N/A` | Agente | Por tarea: `REVIEW.md`, `VALIDATION.md`, `RESULT.md` actualizado |
| 4 | Consolidar veredictos en tabla 10×7 y veredicto global de baseline | Agente | Tabla final + veredicto único |
| 5 | Entregar `RESULT.md` global del plan | Agente | `.ai/tasks/FF-LOCALvNext-000/RESULT.md` |

**Tabla 10×7 (columna por tarea, fila por criterio):**
- Criterios: `Código verificado`, `Tests pasando`, `Migraciones aplicadas`, `Config consistente`, `RESULT.md válido`, `Frontmatter TASK sincronizado`, `Veredicto tarea`

---

## Prohibiciones (estándar del repo)
- Sin código de producto, sin commits/push/merge, sin promociones de estado automáticas.
- Sin cambios semánticos automáticos en ADR, TASK.md o documentación canónica.
- No instalar/actualizar dependencias sin autorización explícita.
- No ejecutar comandos destructivos.
- No modificar secretos ni archivos `.env` (salvo lo indicado en 1b).
- No ampliar scope para aprovechar una edición.
- Gasto incremental de API: `USD 0`; proveedores pagos deshabilitados.

---

## Entregable
`.ai/tasks/FF-LOCALvNext-000/RESULT.md` con:
- Tabla 10×7 completa.
- Veredicto único global entre: `SPRINT_READY` / `CURATION_PARTIALLY_COMPLETED` / `DEVELOPER_DECISION_REQUIRED` / `WORKTREE_BLOCKED`.
- Evidencia `ruta:línea` por cada celda de la tabla.

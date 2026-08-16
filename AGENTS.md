---
document_id: FF-AGENTS-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Reglas para agentes

## Precedencia

1. Código, tests, configuración y migraciones verificadas.
2. `docs/SOURCE_OF_TRUTH.md`.
3. Documentación canónica y ADR aceptados.
4. Contrato `TASK.md` aprobado.
5. Contexto derivado asociado al baseline correcto.

Ante contradicción: detener la inferencia, registrar evidencia y escalar al
Planner o a una persona. No armonizar fuentes silenciosamente.

## Inicio obligatorio

1. Clasificar la tarea: `backend`, `frontend` o `mixed`.
2. Confirmar `task_id`, objetivo, riesgo, baseline y ownership.
3. Cargar solo los documentos declarados en `required_docs`.
4. Solicitar al Explorer un Context Package acotado.
5. Leer el código citado antes de editar.

## Flujo

`PLAN -> EXPLORE -> EXECUTE -> REVIEW -> VALIDATE -> PENDING_ACCEPTANCE`.

Solo una persona puede promover a `DONE`. Si falta contexto, volver a
`EXPLORE`; si falla la implementación, volver a `EXECUTE`; si el plan o la
doctrina son incorrectos, volver a `PLAN`.

## Autonomía

- `low`: ejecución permitida dentro del scope.
- `medium`: ejecución permitida con revisión independiente y validación.
- `high`: `BLOCKED_HIGH_RISK`; requiere nueva decisión humana.
- No instalar o actualizar dependencias sin autorización explícita.
- No ejecutar comandos destructivos.
- No modificar secretos ni archivos `.env`.
- No crear commits, push, merge ni transiciones finales.
- No ampliar scope para “aprovechar” una edición.

## Arquitectura de producto

- Backend: `Router -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL`.
- Schemas Pydantic son contratos de borde, no persistencia.
- Services nuevos no ejecutan ORM directo.
- CRUD no define política de negocio.
- PostgreSQL conserva estado persistente; Redis solo estado temporal con
  ownership explícito.

## Contexto autorizado

- `estructura_Directoriosbackend.txt`,
  `estructura_Directoriosfrontend.txt` o
  `estructura_Directoriostotal.txt`;
- `estructura_de_clases_<YYYY-MM-DD>.xml`;
- bundle Repomix del scope;
- resultados del índice vectorial;
- lecturas directas de código/tests.

Los artefactos derivados orientan; nunca sustituyen la lectura del código
antes de editar. No cargar `docs/archive/source-material/`.

## Escritura concurrente

Una sola ejecución puede poseer una `ownership_key`. Las claves incluyen rutas,
contratos API, dominio, DB/migraciones y documentación canónica. Si existe
intersección, serializar las tareas.

## Evidencia

Cada ejecución debe producir `REVIEW.md`, `VALIDATION.md` y `RESULT.md` usando
los estados `PASS`, `FAIL`, `NOT_RUN`, `UNAVAILABLE`, `BLOCKED` o `N/A`. Un
resumen narrativo sin comando, alcance y salida verificable no es evidencia.

# FF-IMP-001 - Plan de implementacion

## Baseline

- branch: `fix/FF-IMP-001-schema-import-cycle`;
- worktree: `C:/Users/maued/orca/workspaces/FitFlow/fix-FF-IMP-001-schema-import-cycle`;
- base: `develop@5cfcd28b7c2aa0d0e871b72036bdfa4fe59e3827`;
- risk: `medium`;
- ownership: schemas ClassSchedule/GymClass, test de startup y bundle propio.

## Evidencia de entrada

El SCC ejecutable se limita a `class_schedule.py <-> gym_class.py`. El acceso
desde `user.py` y `teacher.py` solo conduce al ciclo. El registro existente
`class_schedule_refs.py` ya rompe otras referencias, pero no contiene el
contrato publico usado por GymClass.

## Diseno

1. crear `gym_class_refs.py` con los schemas GymClass reutilizados por otros
   modulos;
2. ampliar `class_schedule_refs.py` con `ClassSchedulePublic` y hacer que dependa
   solo de `gym_class_refs.py` y `teacher_refs.py`;
3. hacer que ambos schemas principales importen los registros al inicio y
   reexporten los mismos nombres;
4. eliminar `TYPE_CHECKING`, imports al final y `model_rebuild` manual asociados
   al ciclo;
5. verificar identidad, campos, startup, OpenAPI y collection.

El flujo queda lineal:

```text
gym_class_refs -> class_schedule_refs -> class_schedule
               -> gym_class
class_schedule_refs                -> gym_class
```

## Restricciones

- ningun import dentro de funciones, metodos o condicionales;
- ninguna referencia diferida para resolver este ciclo;
- no modificar consumidores, persistencia, dominio ni dependencias;
- todo fallo o gate no ejecutado permanece explicito.

## Validacion

1. build limpio de `backend_test` en proyecto Compose aislado;
2. import de `app.main`, OpenAPI y pytest collection;
3. tests dirigidos enumerados en TASK;
4. wrapper canonico, Ruff, Pyright y `alembic heads`;
5. revision independiente del diff y de contratos;
6. evidencia final en `PENDING_ACCEPTANCE`.

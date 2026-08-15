# Plan de ejecucion

1. Centralizar en `booking_service` la resolucion de session, las transiciones
   de reserva y las reglas de estado; conservar la comprobacion atomica en CRUD.
2. Reemplazar rutas de baja por operaciones conservativas y eliminar la
   desasociacion de `User.person_profile` desde Client.
3. Agregar campos nullable de actor a ClassSchedule con FK `ON DELETE SET NULL`
   y una migracion forward-only.
4. Validar con pruebas dirigidas, metadata/mappers y Alembic sobre
   `fitflow_test` cuando Docker vuelva a estar disponible.

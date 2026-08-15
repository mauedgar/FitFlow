# Plan aprobado

Implementar RRULE RFC 5545 como única recurrencia persistida. La migración
convierte `days_of_week`, verifica el backfill y elimina la columna. La
generación completa solamente sesiones futuras faltantes en una ventana de 15
días, sin reescribir snapshots, Bookings ni sesiones existentes.

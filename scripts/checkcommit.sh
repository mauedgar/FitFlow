#!/bin/bash
# 1. Moverse al directorio del proyecto si es necesario
# 2. Añadir todos los cambios (incluyendo archivos nuevos)
git add -A

# 3. Crear el commit con un mensaje genérico y la fecha actual
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "checkpoint-task: Guardado automático - $TIMESTAMP" --no-verify

echo "Check-point creado con éxito."

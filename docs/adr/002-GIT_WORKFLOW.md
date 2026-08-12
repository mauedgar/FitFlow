Guía de Flujo de Trabajo con Git para el Proyecto FitFlow
Este documento describe el flujo de trabajo estándar de Git que se utilizará en el proyecto FitFlow. Seguir este proceso garantiza un historial de código limpio, facilita la colaboración y previene errores en la rama principal.

El Flujo de Trabajo Principal (Ciclo de una Tarea)
Cada nueva tarea (feature, bugfix, etc.) debe seguir este ciclo completo:

Paso 1: Sincronizar tu Rama Principal
Antes de empezar cualquier trabajo nuevo, asegúrate de que tu copia local de la rama main está actualizada con la versión del repositorio remoto (origin).

bash

# 1. Cámbiate a la rama main

git checkout main

# 2. Descarga los últimos cambios del servidor

git pull origin main
Paso 2: Crear una Nueva Rama
Nunca trabajes directamente en main. Crea una rama específica para tu tarea desde la versión actualizada de main.

Convención de Nombres: tipo/descripcion-corta o tipo/TICKET-ID-descripcion

Tipos comunes: feat, fix, docs, refactor, chore.
bash

# Crea una nueva rama y cámbiate a ella

git checkout -b feat/FIT-2-user-authentication
Paso 3: Trabajar y Hacer Commits
Realiza tus cambios en el código. Haz commits pequeños y atómicos (un commit por cada cambio lógico).

Convención para Mensajes de Commit: tipo(alcance): mensaje [TICKET-ID]

bash

# 1. Añade los archivos que quieres incluir en el commit

git add . # (Añade todos los cambios)
git add src/components/LoginForm.tsx # (Añade un archivo específico)

# 2. Guarda los cambios con un mensaje descriptivo

git commit -m "feat(auth): Crear componente de formulario de login [FIT-2]"
Paso 4: Subir tu Rama al Repositorio Remoto
Cuando estés listo para compartir tu trabajo o crear un Pull Request, sube tu rama al servidor remoto (origin).

bash

# La primera vez que subes la rama, usa el flag -u

git push -u origin feat/FIT-2-user-authentication

# Para subidas posteriores desde la misma rama

git push
Paso 5: Crear un Pull Request (PR)
Ve a la interfaz de GitHub / GitLab:

Aparecerá una notificación para crear un PR desde tu rama recién subida.
Asegúrate de que la base es main y el compare es tu rama.
Escribe un título claro y una descripción detallada de los cambios.
Asigna revisores si es necesario.
Crea el PR.
Paso 6: Fusionar (Merge) el PR y Limpiar
Una vez que el PR es aprobado y las pruebas automáticas pasan:

Haz clic en "Merge pull request".
Confirma la fusión.
Haz clic en "Delete branch" para eliminar la rama del repositorio remoto.
Paso 7: Volver al Paso 1
El ciclo se completa sincronizando tu main local de nuevo y eliminando la rama local que ya no necesitas.

bash

# 1. Vuelve a main

git checkout main

# 2. Actualiza con los cambios que acabas de fusionar

git pull origin main

# 3. Elimina la rama local que ya no se usa

git branch -d feat/FIT-2-user-authentication

Comandos Útiles de Git (Chuleta Rápida)
git status

Muestra el estado de tu directorio de trabajo: qué archivos están modificados, cuáles están preparados para el commit (staged) y cuáles no están siendo rastreados.
git log

Muestra el historial de commits.
git log --oneline --graph: Una vista compacta y gráfica del historial.
git diff

Muestra las diferencias entre tus cambios locales y el último commit.
git diff --staged: Muestra las diferencias de los archivos que ya has añadido al "staging area" (git add).
git restore <archivo>

Descarta los cambios en un archivo, devolviéndolo al estado del último commit. (¡Cuidado, esta acción no se puede deshacer!).
git branch

Lista todas tus ramas locales. La rama actual está marcada con un \*.
git remote -v

Muestra las URLs de tus repositorios remotos.

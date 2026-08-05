📘 README Técnico – FitFlow
TECHNOTON — Tecnología que trabaja para vos
Build. Scale. Automate.
🟦 1. Portada Corporativa
FitFlow – Sistema de Gestión de Gimnasio  
Documentación Técnica (ES)  
Versión: 1.0
Autor: Technoton

Espacio reservado para el logo corporativo (PNG/SVG)

🟦 2. Descripción General del Proyecto
FitFlow es una aplicación web Full Stack, moderna y modular, diseñada para la gestión integral de gimnasios:

Clientes

Profesores

Clases

Agenda de sesiones

Reservas

Membresías

El sistema está construido sobre una arquitectura asíncrona, escalable y desacoplada, con separación clara entre frontend, backend e infraestructura.

🟦 3. Arquitectura General
🔹 3.1 Backend
Lenguaje: Python 3.11+

Framework: FastAPI

ORM: SQLAlchemy 2.0 (async)

Migraciones: Alembic

Base de Datos: PostgreSQL

Servidor: Uvicorn

Autenticación: JWT + Roles

Estilo: Arquitectura modular (app/core/db/models/schemas/api)

🔹 3.2 Frontend
Framework: React 18+

Lenguaje: TypeScript

Build Tool: Vite

UI: Chakra UI

Data Layer: TanStack Query

Routing: React Router DOM

🔹 3.3 Infraestructura
Contenedores: Docker + docker-compose

Servicios: PostgreSQL + Adminer

🟦 4. Estructura del Proyecto
Código
FitFlow/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── vite.config.ts
│
└── docs/
    ├── README_EN.md
    └── identidad_visual.docx
🟦 5. Instalación y Puesta en Marcha
🔹 5.1 Prerrequisitos
Python 3.11+

Node.js 18+

PostgreSQL

Docker (opcional pero recomendado)

🟦 6. Backend – Setup
🔹 6.1 Clonar repositorio
bash
git clone <URL_DEL_REPOSITORIO>
cd FitFlow
🔹 6.2 Crear entorno virtual
bash
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.\.venv\Scripts\activate       # Windows
🔹 6.3 Instalar dependencias
bash
pip install -r requirements.txt
🔹 6.4 Variables de entorno
Crear archivo .env:

Código
DATABASE_URL="postgresql://user:password@host/dbname"
SECRET_KEY="clave_jwt"
🔹 6.5 Ejecutar servidor
bash
uvicorn backend.main:app --reload
Backend disponible en:
http://127.0.0.1:8000

🟦 7. Frontend – Setup
🔹 7.1 Instalar dependencias
bash
cd frontend
npm install
🔹 7.2 Ejecutar servidor
bash
npm run dev
Frontend disponible en:
http://localhost:5173

🟦 8. Migraciones – Alembic
🔹 8.1 Crear migración
bash
alembic revision -m "mensaje" --autogenerate
🔹 8.2 Aplicar migraciones
bash
alembic upgrade head
🟦 9. Arquitectura de Roles
Rol	Permisos
admin	CRUD completo
teacher	Gestión de clases y sesiones propias
client	Reservas, perfil, dashboard
front_desk	Gestión operativa del gimnasio


🟦 10. Endpoints Principales
🔹 10.1 Autenticación
POST /api/v1/login/token

POST /api/v1/users/register

🔹 10.2 Clases
GET /api/v1/gym-classes/

GET /api/v1/gym-classes/{id}

🔹 10.3 Agenda
GET /api/v1/class-schedules/

GET /api/v1/class-sessions/

🔹 10.4 Reservas
POST /api/v1/bookings/

GET /api/v1/bookings/me

DELETE /api/v1/bookings/{id}

🔹 10.5 Personas
GET /api/v1/clients/

GET /api/v1/teachers/

GET /api/v1/memberships/

🟦 11. Testing
🔹 11.1 Ejecutar tests
bash
pytest
🔹 11.2 Tests async
pytest-asyncio

Fixtures para AsyncSession

🟦 12. Despliegue
🔹 12.1 Docker
bash
docker-compose up --build
🔹 12.2 Producción
Configurar variables de entorno

Usar servidor ASGI (Uvicorn/Gunicorn)

Reverse proxy (Nginx)

🟦 13. Flujo Git Profesional (Git Flow)
🔹 13.1 Ramas principales
main → producción, estable

develop → integración de sprints

🔹 13.2 Ramas secundarias
feature/<nombre>

hotfix/<nombre>

release/<versión> (opcional)

🔹 13.3 Flujo de trabajo
✔ Inicio de Sprint
bash
git checkout develop
git pull origin develop
git checkout -b feature/sprint-X
✔ Desarrollo
bash
git add .
git commit -m "feat(sprint-X): descripción"
git push origin feature/sprint-X
✔ Integración del Sprint
bash
git checkout develop
git pull origin develop
git merge feature/sprint-X
git push origin develop
✔ Tag del Sprint
bash
git tag -a sprint-X -m "Cierre Sprint X"
git push origin sprint-X
✔ Release oficial
bash
git checkout main
git pull origin main
git merge origin/develop
git push origin main
Release en GitHub:

Tag: sprint-X

Versión: v0.X.0

🟦 14. Versionado Semántico (SemVer)
Tipo	Ejemplo	Uso
MAJOR	1.0.0	Cambios que rompen compatibilidad
MINOR	0.6.0	Nuevas features sin romper nada
PATCH	0.6.1	Fixes pequeños


🟦 15. Estado Actual del Proyecto
✔ Sprint 6 — Completado
Backend completo y operativo

Routers y servicios finalizados

Rol front_desk integrado

Endpoints de disponibilidad y próxima sesión

Documentación interna actualizada

Release publicado: v0.6.0

Tag asociado: sprint-6

🟦 16. Roadmap Técnico – Sprint 7
Objetivo: MVP Operativo Completo
Integración frontend con backend

Dashboard funcional

Gestión de reservas en tiempo real

Perfil del cliente

Panel del profesor

Panel front_desk

Testing E2E

Preparación para release v0.7.0

🟦 17. Contribución
Estándares
Commits convencionales

Ramas: main, develop, feature/*

Pull requests con revisión obligatoria

Estilo de código
PEP8

Tipado estricto

Linter: flake8

🟦 18. Licencia
Proyecto privado — Technoton.

🟦 19. Conclusión
Este README técnico documenta la arquitectura, instalación, operación y flujo de desarrollo del sistema FitFlow.
Debe mantenerse actualizado en cada sprint y release oficial.

🟦 20 . Entorno de Desarrollo (PowerShell + Alias Maestro)
Para optimizar el flujo de trabajo en Windows, el proyecto incluye un conjunto de alias personalizados configurados en el perfil de PowerShell del desarrollador.
Estos alias permiten activar entornos, iniciar servicios y visualizar logs de manera rápida desde la terminal integrada de VSCode.

✔ Requisitos previos
Windows 10/11
PowerShell 7+
Python 3.11
Docker Desktop
VSCode

🟩 15.1 Activación de entornos
El comando principal es:

Código
env
Sin parámetros, muestra el menú de opciones disponibles.

Comandos disponibles
Comando	Acción
env backend	Activa el entorno virtual del backend (.venv_backend)
env tools	Activa el entorno virtual de herramientas (.venv_tools)
env frontend	Inicia el servidor de desarrollo del frontend (npm run dev)


🟩 15.2 Gestión de Docker y Base de Datos
El proyecto utiliza Docker Compose para levantar el stack completo (backend + Postgres).

Comandos disponibles
Comando	Acción
env db	Levanta todo el stack (docker compose up -d) y muestra los logs del backend
env db backend	Muestra los logs del servicio backend
env db postgres	Muestra los logs del servicio postgres


Estos comandos permiten trabajar con la base de datos y el backend sin necesidad de ejecutar manualmente docker compose.

🟩 15.3 Ubicación de los alias
Los alias se encuentran en el archivo de perfil de PowerShell del desarrollador:

Código
notepad $PROFILE
Este archivo se ejecuta automáticamente cada vez que se abre una terminal PowerShell, por lo que los comandos env están siempre disponibles.


🟩 15.4 Beneficios del sistema de alias
Activación de entornos sin rutas ni .bat

Logs en tiempo real del backend y Postgres

Levantamiento del stack completo con un solo comando

Integración perfecta con VSCode

Evita errores comunes de rutas, entornos y Docker
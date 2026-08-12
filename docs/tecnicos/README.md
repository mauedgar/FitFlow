README Técnico – FitFlow

TECHNOTON

Tecnología que trabaja para vos

Build. Scale. Automate.

1. Portada Corporativa

FitFlow – Sistema de Gestión de GimnasioDocumentación Técnica (ES)Versión: 1.0Autor: Technoton

Espacio reservado para el logo corporativo (PNG/SVG)

2. Descripción General del Proyecto

FitFlow es una aplicación web Full Stack moderna diseñada para gestionar:

Clientes

Profesores

Clases

Agenda de sesiones

Reservas

Membresías

El sistema está construido sobre una arquitectura asíncrona, escalable y modular, con separación clara entre frontend, backend y base de datos.

3. Arquitectura General

3.1 Backend

Lenguaje: Python 3.11+

Framework: FastAPI

ORM: SQLAlchemy 2.0 (async)

Migraciones: Alembic

Base de Datos: PostgreSQL

Servidor: Uvicorn

Autenticación: JWT + Roles(ahora RRAB)

Estilo: Arquitectura modular (app/core/db/models/schemas/api)

3.2 Frontend

Framework: React 18+

Lenguaje: TypeScript

Build Tool: Vite

UI: Chakra UI

Data Layer: TanStack Query

Routing: React Router DOM

3.3 Infraestructura

Contenedores: Docker + docker-compose

Servicios: PostgreSQL + Adminer

4. Estructura del Proyecto(desactualizada)

FitFlow/
│
├── backend/
│ ├── app/
│ │ ├── api/
│ │ ├── core/
│ │ ├── db/
│ │ ├── models/
│ │ ├── schemas/
│ │ └── utils/
│ ├── alembic/
│ ├── tests/
│ └── main.py
│
├── frontend/
│ ├── src/
│ ├── public/
│ └── vite.config.ts
│
└── docs/
├── README_EN.md
└── identidad_visual.docx

5. Instalación y Puesta en Marcha

5.1 Prerrequisitos

Python 3.11+

Node.js 18+

PostgreSQL

Docker (opcional pero recomendado)

6. Backend – Setup

6.1 Clonar repositorio

git clone <URL_DEL_REPOSITORIO>
cd FitFlow

6.2 Crear entorno virtual

python -m venv .venv
source .venv/bin/activate # Linux/Mac
.\.venv\Scripts\activate # Windows

6.3 Instalar dependencias

pip install -r requirements.txt

6.4 Variables de entorno

Crear archivo .env:

DATABASE_URL="postgresql://user:password@host/dbname"
SECRET_KEY="clave_jwt"

6.5 Ejecutar servidor

uvicorn backend.main:app --reload

Backend disponible en: http://127.0.0.1:8000

7. Frontend – Setup

7.1 Instalar dependencias

cd frontend
npm install

7.2 Ejecutar servidor

npm run dev

Frontend disponible en: http://localhost:5173

8. Migraciones – Alembic

8.1 Crear migración

alembic revision -m "mensaje" --autogenerate

8.2 Aplicar migraciones

alembic upgrade head

9. Arquitectura de Roles

Rol

Permisos

admin

CRUD completo de todo el sistema

teacher

Gestión de sus clases y sesiones

client

Reservas, perfil, dashboard

front_desk

Gestión operativa del gimnasio

10. Endpoints Principales(totalmente desactualizado)

10.1 Autenticación

POST /api/v1/login/token
POST /api/v1/users/register

10.2 Clases

GET /api/v1/gym-classes/
GET /api/v1/gym-classes/{id}

10.3 Agenda

GET /api/v1/class-schedules/
GET /api/v1/class-sessions/

10.4 Reservas

POST /api/v1/bookings/
GET /api/v1/bookings/me
DELETE /api/v1/bookings/{id}

10.5 Personas

GET /api/v1/clients/
GET /api/v1/teachers/
GET /api/v1/memberships/

11. Testing

11.1 Ejecutar tests

pytest

11.2 Tests async

pytest-asyncio

Fixtures para AsyncSession

12. Despliegue

12.1 Docker

docker-compose up --build

12.2 Producción

Configurar variables de entorno

Usar servidor ASGI (Uvicorn/Gunicorn)

Reverse proxy (Nginx)

13. Contribución

13.1 Estándares

Commits convencionales

Ramas: main, develop, feature/\*

Pull requests con revisión

13.2 Estilo de código

PEP8

Tipado estricto

Linter: flake8

14. Licencia

Proyecto privado – Technoton.

15. Conclusión

Este README técnico resume la arquitectura, instalación y operación del sistema FitFlow. Es el documento principal del repositorio y debe mantenerse actualizado.

Fin del Documento – README Técnico (ES)

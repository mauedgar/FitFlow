Technical README – FitFlow

TECHNOTON

Technology that works for you

Build. Scale. Automate.

1. Corporate Cover

FitFlow – Gym Management SystemTechnical Documentation (EN)Version: 1.0Author: Technoton

Placeholder for corporate logo (PNG/SVG)

2. Project Overview

FitFlow is a modern Full Stack web application designed to manage:

Clients

Teachers

Gym classes

Class schedules

Sessions

Bookings

Memberships

The system is built on a fully asynchronous architecture, scalable and modular, with a clear separation between frontend, backend, and database layers.

3. System Architecture

3.1 Backend

Language: Python 3.11+

Framework: FastAPI

ORM: SQLAlchemy 2.0 (async)

Migrations: Alembic

Database: PostgreSQL

Server: Uvicorn

Authentication: JWT + Role-based access

Structure: Modular architecture (app/core/db/models/schemas/api)

3.2 Frontend

Framework: React 18+

Language: TypeScript

Build Tool: Vite

UI Library: Chakra UI

Data Layer: TanStack Query

Routing: React Router DOM

3.3 Infrastructure

Containers: Docker + docker-compose

Services: PostgreSQL + Adminer

4. Project Structure

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
└── visual_identity.docx

5. Installation & Setup

5.1 Requirements

Python 3.11+

Node.js 18+

PostgreSQL

Docker (optional but recommended)

6. Backend Setup

6.1 Clone repository

git clone <REPOSITORY_URL>
cd FitFlow

6.2 Create virtual environment

python -m venv .venv
source .venv/bin/activate # Linux/Mac
.\.venv\Scripts\activate # Windows

6.3 Install dependencies

pip install -r requirements.txt

6.4 Environment variables

Create a .env file:

DATABASE_URL="postgresql://user:password@host/dbname"
SECRET_KEY="jwt_secret_key"

6.5 Run backend server

uvicorn backend.main:app --reload

Backend available at: http://127.0.0.1:8000

7. Frontend Setup

7.1 Install dependencies

cd frontend
npm install

7.2 Run development server

npm run dev

Frontend available at: http://localhost:5173

8. Database Migrations (Alembic)

8.1 Create migration

alembic revision -m "message" --autogenerate

8.2 Apply migrations

alembic upgrade head

9. Role Architecture

Role

Permissions

admin

Full CRUD across the system

teacher

Manage own classes and sessions

client

Bookings, profile, dashboard

front_desk

Operational gym management

10. Main Endpoints

10.1 Authentication

POST /api/v1/login/token
POST /api/v1/users/register

10.2 Gym Classes

GET /api/v1/gym-classes/
GET /api/v1/gym-classes/{id}

10.3 Schedules & Sessions

GET /api/v1/class-schedules/
GET /api/v1/class-sessions/

10.4 Bookings

POST /api/v1/bookings/
GET /api/v1/bookings/me
DELETE /api/v1/bookings/{id}

10.5 People

GET /api/v1/clients/
GET /api/v1/teachers/
GET /api/v1/memberships/

11. Testing

11.1 Run tests

pytest

11.2 Async tests

pytest-asyncio

AsyncSession fixtures

12. Deployment

12.1 Docker

docker-compose up --build

12.2 Production

Configure environment variables

Use ASGI server (Uvicorn/Gunicorn)

Reverse proxy (Nginx)

13. Contribution Guidelines

13.1 Standards

Conventional commits

Branches: main, develop, feature/\*

Pull requests with code review

13.2 Code Style

PEP8

Strict typing

Linter: flake8

14. License

Private project – Technoton.

15. Conclusion

This technical README summarizes the architecture, installation, and operation of the FitFlow system. It is the main documentation file for the repository and must remain updated.

End of Document – Technical README (EN)

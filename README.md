# FitFlow - Aplicación de Gestión de Gimnasio

FitFlow es una aplicación web Full Stack moderna diseñada para gestionar clientes, clases y rutinas de un gimnasio.

---

## Stack Tecnológico

- **Backend:**

  - Lenguaje: **Python 3.11+**
  - Framework: **FastAPI**
  - Base de Datos: **PostgreSQL**
  - ORM: **SQLAlchemy**
  - Migraciones: **Alembic**
  - Servidor: **Uvicorn**

- **Frontend:**
  - Framework: **React 18+**
  - Lenguaje: **TypeScript**
  - Herramienta de Build: **Vite**
  - Librería de Componentes: **Chakra UI**
  - Gestor de Paquetes: **npm**

---

## Puesta en Marcha (Setup)

### Prerrequisitos

- Python 3.11 o superior
- Node.js v18 (LTS) o superior
- Una instancia de PostgreSQL corriendo

### Backend Setup

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd FitFlow
    ```
2.  **Crear y activar el entorno virtual:**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```
3.  **Instalar dependencias de Python:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configurar variables de entorno:**

    - Crea un archivo `.env` en la raíz del proyecto copiando `.env.example` (si lo tienes).
    - Añade la URL de tu base de datos: `DATABASE_URL="postgresql://user:password@host/dbname"`

5.  **Ejecutar el servidor de desarrollo:**
    ```bash
    uvicorn backend.main:app --reload
    ```
    El backend estará disponible en `http://127.0.0.1:8000`.

### Frontend Setup

1.  **Navegar a la carpeta del frontend:**
    ```bash
    cd frontend
    ```
2.  **Instalar dependencias de Node.js:**
    ```bash
    npm install
    ```
3.  **Ejecutar el servidor de desarrollo:**
    ```bash
    npm run dev
    ```
    El frontend estará disponible en `http://localhost:5173` (o el puerto que indique Vite).

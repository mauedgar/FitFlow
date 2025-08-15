# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexión a tu base de datos PostgreSQL.
# Formato: "postgresql://user:password@host:port/dbname"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:18246Lu@localhost:5432/postgres"

# El 'engine' es el punto de entrada a la base de datos.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cada instancia de SessionLocal será una sesión de base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Usaremos esta clase base para crear nuestros modelos de SQLAlchemy.
Base = declarative_base()
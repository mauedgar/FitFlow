"""Clase base declarativa para los modelos ORM de FitFlow."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy de la aplicación."""

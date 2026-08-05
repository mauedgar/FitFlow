from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Clase base declarativa para todos los modelos SQLAlchemy."""

    __name__: str

    @declared_attr  # type: ignore[misc]
    def __tablename__(cls) -> str:  # noqa: N805
        """Genera automáticamente el nombre de la tabla a partir del nombre de la clase."""
        return cls.__name__.lower() + "s"

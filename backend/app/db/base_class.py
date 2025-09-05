from sqlalchemy.ext.declarative import as_declarative, declared_attr

# Usamos @as_declarative para poder tener un __tablename__ autogenerado si quisiéramos
# pero lo principal es que esto nos da una 'Base' centralizada.
@as_declarative()
class Base:
    id: any
    __name__: str

    # Genera el __tablename__ automáticamente a partir del nombre de la clase
    # ej: User -> users, GymClass -> gym_classes
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
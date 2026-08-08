
from app.db.base_class import Base

TEMPLATE = """
from app.models.{model_file} import {model}
from app.schemas.{model_file} import {model}Create, {model}Update
from .base import CRUDBase

{var_name} = CRUDBase[{model}, {model}Create, {model}Update]({model})
"""

def generate_crud(model):
    model_file = model.__name__.lower()
    var_name = model_file
    content = TEMPLATE.format(
        model=model.__name__,
        model_file=model_file,
        var_name=var_name,
    )

    path = f"app/crud/crud_{model_file}.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✔ CRUD generado: {path}")


def main():
    for cls in Base.__subclasses__():
        generate_crud(cls)


if __name__ == "__main__":
    main()

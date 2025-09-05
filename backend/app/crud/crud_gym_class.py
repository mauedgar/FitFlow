import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import GymClass, Teacher  # Importamos ambos modelos para las relaciones
from app.schemas.gym_class import GymClassCreate, GymClassUpdate


class CRUDGymClass(CRUDBase[GymClass, GymClassCreate, GymClassUpdate]):
    """
    Operaciones CRUD especializadas para GymClass.
    Hereda los métodos genéricos (get, get_multi, remove) de CRUDBase
    y añade/sobrescribe lógica específica para las clases.
    """

    def create_with_teachers(self, db: Session, *, obj_in: GymClassCreate) -> Optional[GymClass]:
        """
        Crea una nueva GymClass y la asocia con una lista de Teachers existentes.

        Este método es preferible al `create` base porque maneja la compleja
        relación Many-to-Many.

        Args:
            db: La sesión de la base de datos.
            obj_in: El schema Pydantic con los datos de la clase a crear,
                    incluyendo `teacher_ids`.

        Returns:
            El objeto GymClass creado si todos los profesores existen,
            o None si algún ID de profesor es inválido.
        """
        # 1. Validar la existencia de todos los profesores proporcionados.
        #    Hacemos una sola consulta a la BD para ser eficientes.
        found_teachers = db.query(Teacher).filter(Teacher.id.in_(obj_in.teacher_ids)).all()

        # Si la cantidad de profesores encontrados no coincide con la cantidad de IDs
        # solicitados, significa que uno o más IDs son inválidos.
        if len(found_teachers) != len(obj_in.teacher_ids):
            # Devolvemos None para que la capa de la API (endpoint) maneje el error HTTP.
            # El CRUD no debe conocer los detalles de HTTP (como lanzar HTTPException).
            return None

        # 2. Crear el objeto GymClass (sin los teachers todavía).
        #    Usamos el método `create` genérico de la clase base para no repetir código.
        #    Primero, creamos un diccionario sin el campo 'teacher_ids'.
        class_data = obj_in.dict(exclude={"teacher_ids"})
        # Pydantic a veces necesita ayuda para manejar Enums, así que nos aseguramos de
        # que el valor de 'difficulty' sea el string.
        class_data['difficulty'] = class_data['difficulty'].value
        db_obj = self.model(**class_data)

        # 3. Asignar la lista de objetos Teacher a la relación.
        #    SQLAlchemy es lo suficientemente inteligente para entender que esto debe
        #    crear los registros correspondientes en la tabla de asociación.
        db_obj.teachers = found_teachers

        # 4. Guardar en la base de datos y devolver el objeto.
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_with_teachers(self, db: Session, *, db_obj: GymClass, obj_in: GymClassUpdate) -> Optional[GymClass]:
        """
        Actualiza una GymClass existente, incluyendo su lista de profesores.

        Args:
            db: La sesión de la base de datos.
            db_obj: El objeto GymClass SQLAlchemy a actualizar.
            obj_in: El schema Pydantic con los datos a actualizar.

        Returns:
            El objeto GymClass actualizado, o None si algún ID de profesor es inválido.
        """
        # 1. Actualizar los campos simples de la clase usando el método `update` de la base.
        #    Creamos un diccionario solo con los campos que no son la lista de profesores.
        update_data = obj_in.dict(exclude_unset=True, exclude={"teacher_ids"})
        if update_data:
            # Si hay datos que actualizar, llamamos al método base.
            super().update(db=db, db_obj=db_obj, obj_in=update_data)

        # 2. Si se proporcionó una nueva lista de `teacher_ids`, actualizar la relación.
        if obj_in.teacher_ids is not None:
            # Validar que todos los nuevos profesores existan.
            found_teachers = db.query(Teacher).filter(Teacher.id.in_(obj_in.teacher_ids)).all()
            if len(found_teachers) != len(obj_in.teacher_ids):
                return None  # Indica un error a la capa de la API

            # Reemplazar la lista de profesores del objeto con la nueva lista.
            # SQLAlchemy manejará los cambios en la tabla de asociación (borrará los viejos, añadirá los nuevos).
            db_obj.teachers = found_teachers
        
        # 3. Guardar los cambios y devolver.
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_classes_by_teacher(self, db: Session, *, teacher_id: uuid.UUID) -> List[GymClass]:
        """
        Obtiene todas las clases impartidas por un profesor específico.

        Args:
            db: La sesión de la base de datos.
            teacher_id: El UUID del profesor.

        Returns:
            Una lista de objetos GymClass.
        """
        return db.query(self.model).join(Teacher, self.model.teachers).filter(Teacher.id == teacher_id).all()

# Creamos una instancia única del CRUD para ser importada en el resto de la aplicación.
gym_class = CRUDGymClass(GymClass)
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models import Teacher, User
from app.schemas import TeacherCreate, TeacherUpdate

class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    def get_by_full_name(self, db: Session, *, full_name: str) -> Teacher | None:
        return db.query(Teacher).filter(Teacher.full_name == full_name).first()
    
    def create_with_user(self, db: Session, *, obj_in: TeacherCreate, user: User) -> Teacher:
        """
        Crea un perfil de Profesor y lo asocia a un User existente.
        """
        # Creamos la instancia del modelo Teacher. Gracias a la herencia,
        # SQLAlchemy sabe que también debe crear una entrada en la tabla 'persons'.
        db_obj = Teacher(
            # Datos de Person
            name=obj_in.name,
            surname=obj_in.surname,
            passport=obj_in.passport,
            address=obj_in.address,
            # ... otros campos de Person ...
            
            # Datos de Teacher
            bio=obj_in.bio,
            cuil=obj_in.cuil,

            # Asociación con el User
            user=user
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
teacher = CRUDTeacher(Teacher)
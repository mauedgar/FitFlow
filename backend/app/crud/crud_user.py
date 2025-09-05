from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash  


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su dirección de email.
        """
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session = Depends(get_db), *, obj_in: UserCreate) -> User:

        """
        Crea un nuevo usuario en la BD, hasheando la contraseña.
        """
        # 1. Hashea la contraseña que viene del schema
        hashed_password = get_password_hash(obj_in.password)
        
        # 2. Crea la instancia del modelo User de forma explícita
        #    Esto evita cualquier problema con claves extra en el diccionario
        db_obj = User(
            email=obj_in.email,            
            hashed_password=hashed_password,
            role=obj_in.role
        )
        
        # 3. Guarda en la base de datos
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

    # Aquí podríamos sobreescribir el 'update' si, por ejemplo,
    # quisiéramos hashear la contraseña si viene en los datos de actualización.


# Creamos una instancia para usarla en el resto de la aplicación
user = CRUDUser(User)
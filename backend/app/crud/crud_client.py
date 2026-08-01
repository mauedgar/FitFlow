# app/crud/crud_client.py
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models import Client, User # Importa Client, User y Person
from app.schemas import ClientCreate, ClientUpdate # Tus esquemas de Pydantic para Client

class CRUDClient(CRUDBase[Client, ClientCreate, ClientUpdate]):
    
    def get_by_user_id(self, db: Session, *, user_id: uuid.UUID) -> Optional[Client]:
        """
        Obtiene un perfil de Cliente a partir del ID de un User.
        """
        # Accedemos a la relación 'user' definida en el modelo Person (que Client hereda)
        # y filtramos por el id del User.
        return db.query(Client).join(Client.user).filter(User.id == user_id).first()
    
    def create_with_user(self, db: Session, *, obj_in: ClientCreate, user: User) -> Client:
        """
        Crea un perfil de Cliente y lo asocia a un User existente.
        """
        # Creamos la instancia del modelo Client. Debido a la herencia polimórfica,
        # SQLAlchemy manejará la creación de la entrada en la tabla 'persons' automáticamente.
        db_obj = Client(
            # Datos de Person (que vienen de ClientCreate al heredar de PersonCreate)
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            passport=obj_in.passport,
            address=obj_in.address,
            # ... otros campos de Person si ClientCreate los incluye (ej. medical_fit_url, profile_image_url)
            medical_fit_url=obj_in.medical_fit_url, # Si ClientCreate hereda de PersonCreate y tiene estos campos
            profile_image_url=obj_in.profile_image_url,

            # Asociación con el User
            user=user # Asignamos el objeto User directamente a la relación 'user'
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

client = CRUDClient(Client) # Instancia el CRUD para Cliente
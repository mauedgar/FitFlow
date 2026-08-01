# app/crud/crud_class_session.py
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models import ClassSession
from app.schemas import ClassSessionCreate, ClassSessionUpdate

class CRUDClassSession(CRUDBase[ClassSession, ClassSessionCreate, ClassSessionUpdate]):
    # Al igual que ClassSchedule, el CRUD base es suficiente por ahora.
    # Aquí podrías añadir un método para, por ejemplo, obtener sesiones por rango de fechas
    # o para obtener la disponibilidad de una sesión.
    def get_or_create(
        self, 
        db: Session, 
        *, 
        defaults: Optional[Dict[str, Any]] = None, 
        **kwargs: Any
    ) -> Tuple[ClassSession, bool]:
        """
        Busca una instancia del modelo por los criterios en kwargs.
        Si la encuentra, la devuelve.
        Si no, crea una nueva instancia con kwargs y los valores de 'defaults'.

        Returns:
            Tuple[ModelInstance, bool]: Una tupla con la instancia y un booleano 
                                        que es True si se creó una nueva instancia.
        """
        # 1. Intenta obtener el objeto
        instance = db.query(self.model).filter_by(**kwargs).first()
        
        # 2. Si existe, lo devolvemos
        if instance:
            return instance, False
        
        # 3. Si no existe, lo creamos
        # Combinamos los criterios de búsqueda (kwargs) con los datos de creación (defaults)
        create_data = {**kwargs, **(defaults or {})}
        
        # Creamos el objeto en memoria
        instance = self.model(**create_data)
        
        # Lo añadimos a la sesión de la base de datos
        db.add(instance)
        
        # Hacemos un "flush" para que el objeto obtenga su ID de la BD,
        # pero SIN hacer "commit" todavía. El commit se hará al final de la transacción
        # en el endpoint.
        db.flush()
        
        return instance, True


class_session = CRUDClassSession(ClassSession)
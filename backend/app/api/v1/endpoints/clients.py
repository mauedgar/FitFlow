# app/api/endpoints/clients.py
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User, UserRole # Importar para validación de roles

from app import crud, schemas
from app.db.session import get_db
from app.api.deps import (
    get_current_active_user,
    get_current_active_admin,    
    get_current_active_admin_or_self
)
# Asume que tienes un mecanismo de autenticación para obtener el usuario actual
# from app.api.deps import get_current_active_user # Ejemplo de dependencia de usuario autenticado
# from app.api.deps import get_current_active_admin # Para proteger endpoints de creación/gestión

router = APIRouter()

# Endpoint para crear un Cliente para un User existente (similar a Teacher)
@router.post("/{user_id}", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
def create_client_for_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    client_in: schemas.ClientCreate,
    current_user: User = Depends(get_current_active_admin) # Proteger con rol de admin
):
    """
    Crea un perfil de cliente para un usuario existente.
    Requiere permisos de administrador.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario con id {user_id} no fue encontrado.",
        )
    
    if user.person_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario con id {user_id} ya tiene un perfil asociado.",
        )
    # ⭐ Asegurarse de que el usuario tenga el rol CLIENT si le asignas un perfil de cliente
    if user.role != UserRole.CLIENT:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"El usuario con id {user_id} no tiene el rol de {UserRole.CLIENT}. Por favor, actualiza el rol del usuario primero."
         )

    client = crud.client.create_with_user(db=db, obj_in=client_in, user=user)
    
    return client

@router.get("/", response_model=List[schemas.Client])
def read_clients(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_admin) # Proteger con rol de admin
):
    """
    Obtiene una lista de clientes.
    """
    clients = crud.client.get_multi(db, skip=skip, limit=limit)
    return clients

@router.get("/{client_id}", response_model=schemas.Client)
def read_client_by_id(
    *,
    db: Session = Depends(get_db),
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_active_admin_or_self) # Proteger con admin o el propio cliente
):
    """
    Obtiene los detalles de un cliente específico por su ID.
    Requiere permisos de administrador o ser el propio cliente.

    """
    client = crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con id {client_id} no fue encontrado.",
        )
    # Lógica de autorización: Admin o el propio cliente
    if current_user.role != UserRole.ADMIN:
        if not current_user.person_profile or current_user.person_profile.id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este perfil de cliente.")

    return client

@router.put("/{client_id}", response_model=schemas.Client)
def update_client(
    *,
    db: Session = Depends(get_db),
    client_id: uuid.UUID,
    client_in: schemas.ClientUpdate,
    current_user: User = Depends(get_current_active_user) # Verificación más granular
):
    """
    Actualiza el perfil de un cliente. Requiere permisos de administrador o ser el propio cliente.
    """
    client = crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con id {client_id} no fue encontrado.",
        )
    
    # Lógica de autorización: Admin o el propio cliente
    if current_user.role != UserRole.ADMIN:
        if not current_user.person_profile or current_user.person_profile.id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para actualizar este perfil de cliente.")
        
        # Un cliente no debería poder cambiar ciertos campos sensibles de su PersonBase
        # como email_principal si está en PersonBase.
        # Aquí puedes añadir lógica para filtrar `client_in` si no es admin.
        # Por ejemplo, si client_in incluye un campo que solo admin puede cambiar:
        # if client_in.some_sensitive_field is not None:
        #    raise HTTPException(...)

    updated_client = crud.client.update(db, db_obj=client, obj_in=client_in)
    return updated_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    *,
    db: Session = Depends(get_db),
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_active_admin) # Solo Admin puede borrar perfiles de cliente
):
    """
    Elimina un perfil de cliente. Requiere permisos de administrador.
    """
    client = crud.client.get(db, id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con id {client_id} no fue encontrado.",
        )
    
    # Antes de eliminar el perfil de persona (Client), también puedes gestionar el User asociado
    user_to_update = crud.user.get(db, id=client.user.id) # Asumiendo Client tiene una relación 'user'
    if user_to_update:
        user_to_update.person_profile_id = None # Desvincular perfil de persona
        # user_to_update.role = UserRole.DEFAULT_USER # O un rol por defecto si tienes uno
        db.add(user_to_update)
        db.commit()

    crud.client.remove(db, id=client_id)
    return {"message": "Perfil de cliente eliminado exitosamente."}
# Puedes añadir endpoints para actualizar y eliminar clientes.

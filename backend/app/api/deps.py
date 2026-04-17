# app/api/deps.py
from typing import Generator
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud
from app.models.user import User, UserRole # Importa tu modelo User y UserRole
from app.schemas.token import TokenPayload # Importa el TokenPayload que definiste
from app.db.session import SessionLocal
from app.core.config import settings

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/token" # Asegúrate que coincida con tu endpoint de login
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se pudo validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 'sub' debería ser el email del usuario. Usamos crud.user para buscarlo.
    user = crud.user.get_by_email(db, email=token_data.sub) # <-- Necesitarás crud.user.get_by_email
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user

def get_current_active_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de administrador")
    return current_user

def get_current_active_trainer(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de entrenador")
    return current_user

def get_current_active_client(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos de cliente")
    return current_user

# Dependencia para verificar si es admin o el propio usuario/cliente
# Útil para perfiles donde un usuario puede ver el suyo o un admin cualquiera
def get_current_active_admin_or_self(
    current_user: User = Depends(get_current_active_user),
    requested_id: uuid.UUID = None # Este ID vendría de la ruta o del cuerpo de la petición
) -> User:
    # Si es admin, puede acceder
    if current_user.role == UserRole.ADMIN:
        return current_user
    # Si el usuario actual es el mismo que se solicita
    if requested_id and current_user.person_profile and current_user.person_profile.id == requested_id:
        return current_user
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a este recurso.")


#**Notas importantes para `app/api/deps.py`:**
#*   **`crud.user.get_by_email`:** Necesitarás crear este método en tu CRUD de usuarios.
#*   **`settings.API_V1_STR/login/token`:** Asegúrate de que `tokenUrl` coincida exactamente con la ruta de tu endpoint de login.
#*   **`User.person_profile`:** El `get_current_active_admin_or_self` depende de que el `User` tenga un `person_profile` y que ese `person_profile` tenga un `id` que puedas comparar. Esto es crucial para autenticar a un "cliente" o "profesor" por su ID de perfil.
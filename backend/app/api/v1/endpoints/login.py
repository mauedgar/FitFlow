from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Importa solo lo que este endpoint necesita
from app.schemas.token import Token # <-- Usarás el schema de token que creamos
from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.models.user import User # <-- Es buena práctica usar un crud helper, pero por ahora lo hacemos directo
# from app.crud import crud_user

router = APIRouter()
@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autentica un usuario y devuelve un token de acceso.
    """
    # 1. Buscar al usuario por email
    user = db.query(User).filter(User.email == form_data.username).first()

    # 2. Verificar si el usuario existe y la contraseña es correcta
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Crear el token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

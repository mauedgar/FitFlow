# backend/app/api/v1/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import crud, schemas


router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema.
    """
    # 1. Verificar si el usuario ya existe
    db_user = crud.user.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado.",
        )
    
    db_user = crud.user.create( obj_in=user_in, db=db)
    return db_user



